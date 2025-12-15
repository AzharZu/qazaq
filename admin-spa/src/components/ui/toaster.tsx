import * as ToastPrimitives from "@radix-ui/react-toast";
import { useToast } from "./use-toast";
import { cn } from "../../utils/cn";

export function Toaster() {
  const { toasts, dismiss } = useToast();
  return (
    <ToastPrimitives.Viewport className="fixed top-6 right-6 z-50 flex w-[320px] flex-col gap-2 outline-none">
      {toasts.map((toast) => (
        <ToastPrimitives.Root
          key={toast.id}
          className={cn(
            "rounded-md border border-border bg-white shadow-lg p-3 text-sm text-gray-900",
            toast.variant === "destructive" && "border-red-200 bg-red-50 text-red-900"
          )}
          onOpenChange={(open) => !open && dismiss(toast.id)}
          open
        >
          {toast.title && <div className="font-semibold">{toast.title}</div>}
          {toast.description && <div className="text-gray-600">{toast.description}</div>}
        </ToastPrimitives.Root>
      ))}
    </ToastPrimitives.Viewport>
  );
}
