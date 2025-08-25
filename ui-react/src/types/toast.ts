export type MessageCategory = 'info' | 'error' | 'success';

export type ToastMessage =  {
  message: string;
  category: MessageCategory
}