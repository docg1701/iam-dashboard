import { useToast as useToastOriginal } from "@/components/ui/toast";

export const useToast = () => {
  const { addToast, removeToast, toasts } = useToastOriginal();

  const toast = (props: Parameters<typeof addToast>[0]) => {
    return addToast(props);
  };

  return {
    toast,
    dismiss: removeToast,
    toasts,
  };
};
