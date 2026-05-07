import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:     "bg-accent text-background hover:bg-accent/90",
        destructive: "bg-accent-danger text-background hover:bg-accent-danger/90",
        outline:     "border border-border bg-transparent hover:bg-surface-hover text-text-primary",
        secondary:   "bg-surface hover:bg-surface-hover text-text-primary",
        ghost:       "hover:bg-surface-hover text-text-primary",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm:      "h-8 rounded-md px-3 text-xs",
        lg:      "h-10 rounded-md px-8",
        icon:    "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  pendingText?: string;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  disabled,
  pendingText,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled}
      {...props}
    >
      {disabled && pendingText ? pendingText : children}
    </Comp>
  );
}

export { buttonVariants };
