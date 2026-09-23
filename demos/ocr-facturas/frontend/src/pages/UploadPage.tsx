import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { useInvoiceStore } from '../stores/useInvoiceStore';
import { useToastStore } from '../stores/useToastStore';
import FileDropzone from '../components/upload/FileDropzone';
import UploadProgress from '../components/upload/UploadProgress';

interface UploadItem {
  file: File;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string | null;
  invoiceId?: string;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { uploadInvoice } = useInvoiceStore();
  const addToast = useToastStore((s) => s.addToast);
  const [uploads, setUploads] = useState<UploadItem[]>([]);

  const handleFilesAccepted = useCallback(
    async (files: File[]) => {
      const newUploads: UploadItem[] = files.map((file) => ({
        file,
        status: 'uploading' as const,
      }));
      setUploads((prev) => [...prev, ...newUploads]);

      // Process each file sequentially
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const uploadIndex = uploads.length + i;

        // Update to uploading
        setUploads((prev) =>
          prev.map((u, idx) => (idx === uploadIndex ? { ...u, status: 'uploading' } : u)),
        );

        try {
          // Update to processing
          setUploads((prev) =>
            prev.map((u, idx) => (idx === uploadIndex ? { ...u, status: 'processing' } : u)),
          );

          const result = await uploadInvoice(file);

          // Update to completed
          setUploads((prev) =>
            prev.map((u, idx) =>
              idx === uploadIndex ? { ...u, status: 'completed', invoiceId: result.invoice_id } : u,
            ),
          );

          addToast('success', `Factura "${file.name}" procesada exitosamente.`);
        } catch (err) {
          const errorMsg = (err as { detail?: string })?.detail || 'Error al procesar la factura.';

          setUploads((prev) =>
            prev.map((u, idx) =>
              idx === uploadIndex ? { ...u, status: 'failed', error: errorMsg } : u,
            ),
          );

          addToast('error', `Error al procesar "${file.name}": ${errorMsg}`);
        }
      }
    },
    [uploads.length, uploadInvoice, addToast],
  );

  const hasActiveUploads = uploads.some(
    (u) => u.status === 'uploading' || u.status === 'processing',
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="text-center">
        <h2 className="text-lg font-semibold text-gray-900">Subir Facturas</h2>
        <p className="mt-1 text-sm text-gray-500">
          Subí archivos PDF o imágenes de facturas para procesar con OCR.
        </p>
      </div>

      <FileDropzone onFilesAccepted={handleFilesAccepted} disabled={hasActiveUploads} />

      {/* Upload list */}
      {uploads.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">Archivos ({uploads.length})</h3>
          {uploads.map((upload, idx) => (
            <div key={idx} className="relative">
              <UploadProgress
                fileName={upload.file.name}
                fileSize={upload.file.size}
                status={upload.status}
                error={upload.error}
                invoiceId={upload.invoiceId}
              />
              {/* View detail button for completed uploads */}
              {upload.status === 'completed' && upload.invoiceId && (
                <button
                  onClick={() => navigate(`/invoices/${upload.invoiceId}`)}
                  className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700"
                >
                  <FileText className="h-3 w-3" />
                  Ver detalle
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
