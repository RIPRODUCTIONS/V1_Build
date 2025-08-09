"use client";

type Props = {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
}: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded bg-white p-6 shadow">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="mt-2 text-gray-700">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onCancel} className="px-4 py-2 rounded border">
            {cancelText}
          </button>
          <button onClick={onConfirm} className="px-4 py-2 rounded bg-red-600 text-white">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
