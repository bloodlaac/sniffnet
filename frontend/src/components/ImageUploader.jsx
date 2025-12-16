"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export default function ImageUploader({ valueFile, onChange, disabled = false }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!valueFile) {
      setPreviewUrl(null);
      return undefined;
    }

    const url = URL.createObjectURL(valueFile);
    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [valueFile]);

  const handleFiles = useCallback(
    (files) => {
      if (disabled || !files || !files.length) return;
      const [file] = files;
      if (file && file.type && file.type.startsWith("image/")) {
        onChange?.(file);
      }
    },
    [onChange, disabled]
  );

  const onDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e) => {
    e.preventDefault();
  };

  const openFileDialog = () => {
    if (disabled) return;
    inputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div
        className={`rounded-2xl border border-dashed border-blue-200 bg-blue-50/60 p-6 text-center transition hover:border-blue-300 hover:bg-blue-50 ${
          disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
        }`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onClick={openFileDialog}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          disabled={disabled}
        />
        <p className="text-lg font-semibold text-slate-900 mb-1">
          Перетащите фото сюда
        </p>
        <p className="text-sm text-slate-600">
          или нажмите, чтобы выбрать файл
        </p>
        {previewUrl && (
          <div className="mt-5 flex justify-center">
            <img
              src={previewUrl}
              alt="Предпросмотр"
              className="max-h-72 rounded-2xl border border-slate-100 shadow-lg object-contain"
            />
          </div>
        )}
      </div>
    </div>
  );
}
