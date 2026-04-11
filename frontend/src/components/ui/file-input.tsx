import React, { useRef, useState } from "react";
import { UploadCloud, File, X } from "lucide-react";
import clsx from "clsx";

interface FileInputProps {
  onFileChange: (file: File | null) => void;
  accept?: string;
  id?: string;
}

export function FileInput({ onFileChange, accept = ".pdf", id = "file-upload" }: FileInputProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    console.log('Document upload - File selected:', file?.name, 'Size:', file?.size, 'Type:', file?.type);
    setSelectedFile(file);
    onFileChange(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
    onFileChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full">
      <input
        type="file"
        id={id}
        ref={fileInputRef}
        onChange={handleFileChange}
        accept={accept}
        className="hidden"
      />
      
      {!selectedFile ? (
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl px-4 py-6 text-slate-500 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50/50 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-slate-700 dark:text-slate-400 dark:hover:border-blue-500 dark:hover:text-blue-400 dark:hover:bg-slate-800/50"
        >
          <UploadCloud className="h-5 w-5" />
          <span className="font-medium">Click to upload PDF</span>
        </button>
      ) : (
        <div className="flex items-center justify-between border border-slate-200 rounded-xl px-4 py-3 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50">
          <div className="flex items-center gap-3 overflow-hidden text-ellipsis whitespace-nowrap">
            <span className="p-2 shrink-0 bg-white border border-slate-200 rounded-lg dark:bg-slate-800 dark:border-slate-700">
              <File className="h-4 w-4 text-blue-500" />
            </span>
            <span className="text-sm font-medium text-slate-700 truncate dark:text-slate-300">
              {selectedFile.name}
            </span>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="p-2 shrink-0 text-slate-400 hover:text-red-500 transition-colors focus:outline-none"
            aria-label="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
