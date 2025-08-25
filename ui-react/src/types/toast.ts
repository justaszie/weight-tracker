export type ToastMessageCategory = 'info' | 'error' | 'success';

export type ToastMessage = {
  message: string;
  category: ToastMessageCategory;
};

export type ShowToastFn = (category:ToastMessageCategory, message: string) => void;