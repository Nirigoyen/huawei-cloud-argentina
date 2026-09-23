import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';
import { validateFile, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES } from '../../utils/validators';

interface FileDropzoneProps {
  onFilesAccepted: (files: File[]) => void;
  disabled?: boolean;
}

export default function FileDropzone({ onFilesAccepted, disabled = false }: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const validFiles: File[] = [];
      const errors: string[] = [];

      for (const file of acceptedFiles) {
        const error = validateFile(file);
        if (error) {
          errors.push(`${file.name}: ${error}`);
        } else {
          validFiles.push(file);
        }
      }

      if (errors.length > 0) {
        alert(errors.join('\n'));
      }

      if (validFiles.length > 0) {
        onFilesAccepted(validFiles);
      }
    },
    [onFilesAccepted],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    multiple: true,
    maxSize: MAX_FILE_SIZE_BYTES,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/gif': ['.gif'],
      'image/webp': ['.webp'],
      'image/svg+xml': ['.svg'],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
        isDragActive
          ? 'border-primary-500 bg-primary-50'
          : disabled
            ? 'cursor-not-allowed border-gray-200 bg-gray-50'
            : 'border-gray-300 bg-white hover:border-primary-400 hover:bg-primary-50/50'
      }`}
    >
      <input {...getInputProps()} />

      <div className="mb-4 rounded-full bg-primary-100 p-4">
        {isDragActive ? (
          <FileText className="h-8 w-8 text-primary-600" />
        ) : (
          <Upload className="h-8 w-8 text-primary-600" />
        )}
      </div>

      {isDragActive ? (
        <p className="text-lg font-medium text-primary-600">Soltá los archivos aquí...</p>
      ) : (
        <>
          <p className="text-lg font-medium text-gray-700">
            Arrastrá y soltá archivos aquí, o{' '}
            <span className="text-primary-600">hacé clic para seleccionar</span>
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Tipos permitidos: {ALLOWED_EXTENSIONS.join(', ')}
          </p>
          <p className="mt-1 text-sm text-gray-500">Tamaño máximo: 15 MB por archivo</p>
        </>
      )}
    </div>
  );
}
