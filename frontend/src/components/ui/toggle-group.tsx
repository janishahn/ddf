import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const toggleGroupVariants = cva(
  "inline-flex items-center gap-1 rounded-[var(--radius-inset)] bg-[hsl(var(--muted))] p-1",
  {
    variants: {
      size: {
        default: "text-sm",
        sm: "text-xs",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
);

const toggleItemVariants = cva(
  "inline-flex items-center justify-center rounded-[var(--radius-tight)] px-3 py-1.5 font-medium text-[hsl(var(--muted-foreground))] transition-colors data-[state=on]:text-[hsl(var(--foreground))]",
  {
    variants: {
      size: {
        default: "text-sm",
        sm: "text-xs",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
);

const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root> &
    VariantProps<typeof toggleGroupVariants>
>(({ className, size, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    className={cn(toggleGroupVariants({ size }), className)}
    {...props}
  />
));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> &
    VariantProps<typeof toggleItemVariants>
>(({ className, size, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(toggleItemVariants({ size }), className)}
    {...props}
  />
));
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { ToggleGroup, ToggleGroupItem };
