import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { Menu, X } from "lucide-react";

import { cn } from "@/lib/utils";

const SIDEBAR_COOKIE_NAME = "sidebar:state";
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
const SIDEBAR_WIDTH = "16rem";
const SIDEBAR_WIDTH_MOBILE = "18rem";
const SIDEBAR_WIDTH_ICON = "3rem";
const SIDEBAR_KEYBOARD_SHORTCUT = "b";

const SidebarContext = React.createContext(null);

function useSidebar() {
  const context = React.useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}

const SidebarProvider = React.forwardRef(
  (
    {
      defaultOpen = true,
      open: openProp,
      onOpenChange: onOpenChangeProp,
      className,
      style,
      children,
      ...props
    },
    ref,
  ) => {
    const isMobile = typeof window === "undefined" ? false : window.innerWidth < 768;
    const [openState, setOpenState] = React.useState(() => {
      if (typeof openProp === "boolean") {
        return openProp;
      }
      if (typeof window === "undefined") {
        return defaultOpen;
      }
      const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith(SIDEBAR_COOKIE_NAME))
        ?.split("=")[1];
      if (cookieValue) {
        return cookieValue === "true";
      }
      return defaultOpen;
    });

    const open = openProp ?? openState;
    const onOpenChange = React.useCallback(
      (value) => {
        setOpenState(value);
        onOpenChangeProp?.(value);

        if (typeof document !== "undefined") {
          const date = new Date();
          date.setTime(date.getTime() + SIDEBAR_COOKIE_MAX_AGE * 1000);
          document.cookie = `${SIDEBAR_COOKIE_NAME}=${value}; path=/; expires=${date.toUTCString()}`;
        }
      },
      [onOpenChangeProp],
    );

    React.useEffect(() => {
      const handleKeyDown = (event) => {
        if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
          event.preventDefault();
          onOpenChange(!open);
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [open, onOpenChange]);

    const state = open ? "expanded" : "collapsed";

    const context = React.useMemo(
      () => ({
        state,
        open,
        setOpen: onOpenChange,
        isMobile,
        openMobile: false,
        setOpenMobile: () => {},
      }),
      [state, open, onOpenChange, isMobile],
    );

    return (
      <SidebarContext.Provider value={context}>
        <div
          style={
            {
              "--sidebar-width": SIDEBAR_WIDTH,
              "--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
              ...style,
            }
          }
          className={cn(
            "group/sidebar-wrapper flex min-h-svh w-full has-[[data-variant=inset]]:bg-sidebar",
            className,
          )}
          ref={ref}
          {...props}
        >
          {children}
        </div>
      </SidebarContext.Provider>
    );
  },
);
SidebarProvider.displayName = "SidebarProvider";

const Sidebar = React.forwardRef(
  ({ side = "left", variant = "sidebar", collapsible = "offcanvas", className, ...props }, ref) => {
    const { isMobile, state, openMobile, setOpenMobile } = useSidebar();

    if (collapsible === "none") {
      return (
        <div
          className={cn("flex h-full w-[--sidebar-width] flex-col bg-sidebar text-sidebar-foreground", className)}
          ref={ref}
          {...props}
        />
      );
    }

    if (isMobile) {
      return (
        <sheet.Sheet open={openMobile} onOpenChange={setOpenMobile} {...props}>
          <sheet.SheetContent side={side} className="w-[--sidebar-width-mobile] bg-sidebar p-0 text-sidebar-foreground">
            <div className="flex h-full w-full flex-col">{props.children}</div>
          </sheet.SheetContent>
        </sheet.Sheet>
      );
    }

    return (
      <div
        className="group peer/sidebar-toggle relative hidden md:block"
        data-state={state}
        data-collapsible={collapsible}
        data-variant={variant}
      >
        <div
          ref={ref}
          className={cn(
            "duration-200 relative hidden h-svh w-[--sidebar-width] flex-col bg-sidebar text-sidebar-foreground transition-[width,margin] ease-linear after:absolute after:inset-y-0 after:right-0 after:w-px after:bg-border group-data-[state=collapsed]/sidebar-wrapper:w-[--sidebar-width-icon] group-data-[state=collapsed]/sidebar-wrapper:overflow-hidden md:flex",
            className,
          )}
          {...props}
        />
      </div>
    );
  },
);
Sidebar.displayName = "Sidebar";

const SidebarTrigger = React.forwardRef(
  ({ className, onClick, ...props }, ref) => {
    const { toggleSidebar } = useSidebarContext();

    return (
      <button
        ref={ref}
        data-sidebar="trigger"
        onClick={(event) => {
          onClick?.(event);
          toggleSidebar();
        }}
        className={cn("inline-flex items-center justify-center rounded-md p-2 text-sidebar-foreground", className)}
        {...props}
      >
        <Menu />
      </button>
    );
  },
);
SidebarTrigger.displayName = "SidebarTrigger";

const useSidebarContext = () => {
  const { setOpen } = useSidebar();
  return {
    toggleSidebar: () => setOpen((open) => !open),
  };
};

const SidebarRail = React.forwardRef(
  ({ className, ...props }, ref) => {
    const { toggleSidebar } = useSidebarContext();

    return (
      <button
        ref={ref}
        data-sidebar="rail"
        aria-label="Toggle Sidebar"
        onClick={toggleSidebar}
        className={cn("absolute inset-y-0 left-full hidden w-4 translate-x-1/2 transition-all ease-linear peer-hover/sidebar-toggle:bg-sidebar-accent group-data-[state=collapsed]/sidebar-wrapper:peer-hover/sidebar-toggle:w-4 group-data-[state=collapsed]/sidebar-wrapper:peer-hover/sidebar-toggle:translate-x-0 after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 hover:after:bg-sidebar-border md:peer-group-[.group-data-[collapsible=icon]]/sidebar-wrapper:flex", className)}
        {...props}
      />
    );
  },
);
SidebarRail.displayName = "SidebarRail";

const SidebarInset = React.forwardRef(
  ({ className, ...props }, ref) => (
    <main
      ref={ref}
      className={cn(
        "relative flex min-h-svh flex-1 flex-col bg-background group-data-[variant=inset]/sidebar-wrapper:bg-sidebar @supports (margin-inline: max(var(--gutter))):group-data-[variant=inset]/sidebar-wrapper:p-[max(var(--gutter),env(safe-area-inset-left))] @supports (margin-inline: max(var(--gutter))):group-data-[variant=inset]/sidebar-wrapper:margin-inline-start:calc(var(--sidebar-width) * -1) @supports (margin-inline: max(var(--gutter))):group-data-[variant=inset]/sidebar-wrapper:pe-[max(var(--gutter),env(safe-area-inset-right))]",
        className,
      )}
      {...props}
    />
  ),
);
SidebarInset.displayName = "SidebarInset";

const sidebarMenuButtonVariants = cva(
  "peer/menu-button relative flex w-full items-center gap-2 overflow-hidden rounded-md px-2 py-1.5 text-left outline-none ring-sidebar-ring transition-[width,height,padding] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 group-data-[collapsible=icon]/sidebar-wrapper:!size-8 group-data-[collapsible=icon]/sidebar-wrapper:!p-0 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0 aria-disabled:pointer-events-none aria-disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        outline: "border border-sidebar-border bg-white hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:border-sidebar-accent",
      },
      size: {
        default: "h-8 px-2",
        sm: "h-7 px-2 text-xs",
        lg: "h-12 px-2 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const SidebarMenuButton = React.forwardRef(
  ({ asChild = false, isActive = false, variant = "default", size = "default", tooltip, className, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    const button = (
      <Comp
        ref={ref}
        data-active={isActive}
        data-sidebar="menu-button"
        className={cn(sidebarMenuButtonVariants({ variant, size }), className)}
        {...props}
      />
    );

    if (!tooltip) {
      return button;
    }

    return (
      <tooltip.Tooltip>
        <tooltip.TooltipTrigger asChild>{button}</tooltip.TooltipTrigger>
        <tooltip.TooltipContent side="right" className="pointer-events-none">
          {tooltip}
        </tooltip.TooltipContent>
      </tooltip.Tooltip>
    );
  },
);
SidebarMenuButton.displayName = "SidebarMenuButton";

const SidebarMenuItem = React.forwardRef(
  ({ className, ...props }, ref) => (
    <li ref={ref} className={cn("group/menu-item relative", className)} {...props} />
  ),
);
SidebarMenuItem.displayName = "SidebarMenuItem";

const SidebarMenuSub = React.forwardRef(
  ({ className, ...props }, ref) => (
    <ul
      ref={ref}
      data-sidebar="menu-sub"
      className={cn("border-sidebar-border px-2 py-0.5 group-data-[collapsible=icon]/sidebar-wrapper:hidden", className)}
      {...props}
    />
  ),
);
SidebarMenuSub.displayName = "SidebarMenuSub";

const SidebarMenuSubItem = React.forwardRef(
  ({ ...props }, ref) => <li ref={ref} {...props} />,
);
SidebarMenuSubItem.displayName = "SidebarMenuSubItem";

const SidebarMenuSubButton = React.forwardRef(
  ({ asChild = false, size = "md", isActive, className, ...props }, ref) => {
    const Comp = asChild ? Slot : "a";

    return (
      <Comp
        ref={ref}
        data-active={isActive}
        data-sidebar="menu-sub-button"
        data-size={size}
        className={cn(
          "relative flex h-7 min-w-0 -mx-2 items-center gap-2 overflow-hidden rounded-md px-2 outline-none ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0 [&>svg]:text-sidebar-accent-foreground",
          size === "sm" && "text-xs",
          size === "md" && "text-sm",
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarMenuSubButton.displayName = "SidebarMenuSubButton";

const SidebarMenuBadge = React.forwardRef(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      data-sidebar="menu-badge"
      className={cn(
        "pointer-events-none absolute right-1 flex h-5 min-w-5 items-center justify-center rounded-md bg-sidebar-primary px-1 text-xs font-medium text-sidebar-primary-foreground group-data-[collapsible=icon]/sidebar-wrapper:right-[-10px]",
        className,
      )}
      {...props}
    />
  ),
);
SidebarMenuBadge.displayName = "SidebarMenuBadge";

const SidebarMenu = React.forwardRef(
  ({ className, ...props }, ref) => (
    <ul ref={ref} data-sidebar="menu" className={cn("flex w-full min-w-0 flex-col gap-1", className)} {...props} />
  ),
);
SidebarMenu.displayName = "SidebarMenu";

const SidebarMenuSeparator = React.forwardRef(
  (
    {
      className,
      ...props
    },
    ref,
  ) => (
    <li
      ref={ref}
      data-sidebar="menu-separator"
      role="separator"
      className={cn("mx-2 my-1 h-px bg-sidebar-border group-data-[collapsible=icon]/sidebar-wrapper:mx-0", className)}
      {...props}
    />
  ),
);
SidebarMenuSeparator.displayName = "SidebarMenuSeparator";

export {
  Sidebar,
  SidebarProvider,
  useSidebar,
  SidebarTrigger,
  SidebarRail,
  SidebarInset,
  SidebarMenuButton,
  SidebarMenuButtonVariants: sidebarMenuButtonVariants,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarMenu,
  SidebarMenuSeparator,
  SidebarMenuBadge,
};
