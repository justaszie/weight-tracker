export type ToastMessageCategory = 'info' | 'error' | 'success';

export type ToastMessage =  {
  message: string;
  category: ToastMessageCategory;
};