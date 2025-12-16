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
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          disabled ? "opacity-60 cursor-not-allowed" : "hover:border-blue-400"
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
        <p className="text-lg font-semibold mb-2">Перетащите фото сюда</p>
        <p className="text-sm text-gray-600">или нажмите, чтобы выбрать файл</p>
        {previewUrl && (
          <div className="mt-4 flex justify-center">
            <img
              src={previewUrl}
              alt="Предпросмотр"
              className="max-h-64 rounded shadow-md object-contain"
            />
          </div>
        )}
      </div>
    </div>
  );
}
