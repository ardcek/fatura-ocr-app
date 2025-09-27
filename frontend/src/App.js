import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [currentInvoice, setCurrentInvoice] = useState(null);
  const [invoiceResults, setInvoiceResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recentInvoices, setRecentInvoices] = useState([]);

  const API_BASE = "http://localhost:8000";

  useEffect(() => {
    // Sayfa yüklendiğinde son faturaları getir
    fetchRecentInvoices();
  }, []);

  const fetchRecentInvoices = async () => {
    try {
      const res = await fetch(`${API_BASE}/invoices?limit=10`);
      const data = await res.json();
      setRecentInvoices(data);
    } catch (err) {
      console.error("Failed to fetch recent invoices:", err);
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError("Lütfen bir dosya seçin");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error(`Upload failed: ${uploadRes.statusText}`);
      }

      const uploadData = await uploadRes.json();
      setCurrentInvoice(uploadData);

      // OCR işlemini başlat
      await fetch(`${API_BASE}/process/${uploadData.id}`, {
        method: "POST",
      });

      // Sonuçları bekle
      pollForResults(uploadData.id);
      
    } catch (err) {
      setError(`Upload hatası: ${err.message}`);
      setLoading(false);
    }
  };

  const pollForResults = async (invoiceId) => {
    const maxAttempts = 30; // 30 saniye max bekleme
    let attempts = 0;

    const poll = async () => {
      attempts++;
      
      try {
        const res = await fetch(`${API_BASE}/results/${invoiceId}`);
        const data = await res.json();

        if (data.status === "ocr_processed" || data.status === "validated") {
          setInvoiceResults(data);
          setLoading(false);
          fetchRecentInvoices(); // Listeyi yenile
          return;
        } else if (data.status === "error") {
          setError("OCR işlemi sırasında hata oluştu");
          setLoading(false);
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // 1 saniye sonra tekrar dene
        } else {
          setError("İşlem zaman aşımına uğradı");
          setLoading(false);
        }
      } catch (err) {
        setError(`Sonuç alınamadı: ${err.message}`);
        setLoading(false);
      }
    };

    poll();
  };

  const handleFieldValidation = async (fieldName, value) => {
    if (!currentInvoice) return;

    try {
      const res = await fetch(`${API_BASE}/validate/${currentInvoice.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          field_name: fieldName,
          corrected_value: value,
          user_id: "admin"
        }),
      });

      if (res.ok) {
        // Sonuçları yenile
        const updatedRes = await fetch(`${API_BASE}/results/${currentInvoice.id}`);
        const updatedData = await updatedRes.json();
        setInvoiceResults(updatedData);
      }
    } catch (err) {
      console.error("Validation error:", err);
    }
  };

  const sendToERP = async () => {
    if (!currentInvoice) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/erp/send/${currentInvoice.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          invoice_id: currentInvoice.id,
          action: "CREATE"
        }),
      });

      if (res.ok) {
        alert("Fatura ERP sistemine gönderildi!");
        fetchRecentInvoices();
      } else {
        alert("ERP gönderimi başarısız!");
      }
    } catch (err) {
      alert(`ERP hatası: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString('tr-TR');
  };

  const formatMoney = (amount) => {
    if (!amount) return "N/A";
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount);
  };

  const getStatusColor = (status) => {
    const colors = {
      uploaded: "#ffa726",
      ocr_processed: "#42a5f5",
      validated: "#66bb6a",
      sent_to_erp: "#26a69a",
      erp_confirmed: "#4caf50",
      error: "#ef5350"
    };
    return colors[status] || "#999";
  };

  const getStatusText = (status) => {
    const texts = {
      uploaded: "Yüklendi",
      ocr_processed: "OCR Tamamlandı",
      validated: "Doğrulandı",
      sent_to_erp: "ERP'ye Gönderildi",
      erp_confirmed: "ERP Onaylandı",
      error: "Hata"
    };
    return texts[status] || status;
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📄 Akıllı Fatura OCR Sistemi</h1>
        <p>Fatura, irsaliye ve makbuzlarınızı otomatik olarak okuyun ve ERP sisteminize aktarın</p>
      </header>

      <main className="main-content">
        {/* Upload Section */}
        <section className="upload-section">
          <h2>📤 Fatura Yükle</h2>
          <div className="upload-area">
            <input
              type="file"
              accept="image/*,.pdf"
              onChange={(e) => setFile(e.target.files[0])}
              className="file-input"
            />
            <button 
              onClick={handleFileUpload} 
              disabled={!file || loading}
              className="upload-btn"
            >
              {loading ? "⏳ İşleniyor..." : "📤 Yükle ve İşle"}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
        </section>

        {/* Results Section */}
        {invoiceResults && (
          <section className="results-section">
            <h2>🔍 OCR Sonuçları</h2>
            <div className="results-container">
              <div className="status-badge" style={{backgroundColor: getStatusColor(invoiceResults.status)}}>
                {getStatusText(invoiceResults.status)}
              </div>
              
              <div className="results-grid">
                <div className="field-group">
                  <label>Fatura Numarası:</label>
                  <EditableField 
                    value={invoiceResults.invoice_number} 
                    onSave={(value) => handleFieldValidation('invoice_number', value)}
                  />
                </div>

                <div className="field-group">
                  <label>Tarih:</label>
                  <EditableField 
                    value={formatDate(invoiceResults.invoice_date)} 
                    onSave={(value) => handleFieldValidation('invoice_date', value)}
                  />
                </div>

                <div className="field-group">
                  <label>Firma Adı:</label>
                  <EditableField 
                    value={invoiceResults.company_name} 
                    onSave={(value) => handleFieldValidation('company_name', value)}
                  />
                </div>

                <div className="field-group">
                  <label>Vergi Numarası:</label>
                  <EditableField 
                    value={invoiceResults.company_tax_number} 
                    onSave={(value) => handleFieldValidation('company_tax_number', value)}
                  />
                </div>

                <div className="field-group">
                  <label>Toplam Tutar:</label>
                  <EditableField 
                    value={formatMoney(invoiceResults.total_amount)} 
                    onSave={(value) => handleFieldValidation('total_amount', value)}
                  />
                </div>

                <div className="field-group">
                  <label>KDV Tutarı:</label>
                  <EditableField 
                    value={formatMoney(invoiceResults.vat_amount)} 
                    onSave={(value) => handleFieldValidation('vat_amount', value)}
                  />
                </div>

                <div className="field-group">
                  <label>Güven Skoru:</label>
                  <div className="confidence-score">
                    {(invoiceResults.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="action-buttons">
                <button 
                  onClick={sendToERP} 
                  disabled={loading || invoiceResults.status === 'sent_to_erp'}
                  className="erp-btn"
                >
                  {invoiceResults.status === 'sent_to_erp' ? 
                    "✅ ERP'ye Gönderildi" : "📤 ERP'ye Gönder"}
                </button>
              </div>
            </div>
          </section>
        )}

        {/* Recent Invoices */}
        <section className="recent-section">
          <h2>📋 Son Faturalar</h2>
          <div className="invoices-list">
            {recentInvoices.map(invoice => (
              <div key={invoice.id} className="invoice-item">
                <div className="invoice-info">
                  <strong>{invoice.filename}</strong>
                  <span>#{invoice.invoice_number || 'N/A'}</span>
                  <span>{formatDate(invoice.created_at)}</span>
                </div>
                <div className="invoice-status" style={{color: getStatusColor(invoice.status)}}>
                  {getStatusText(invoice.status)}
                </div>
                <div className="invoice-amount">
                  {formatMoney(invoice.total_amount)}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

// Düzenlenebilir alan komponenti
function EditableField({ value, onSave }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value || '');

  const handleSave = () => {
    if (editValue !== value) {
      onSave(editValue);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value || '');
    setIsEditing(false);
  };

  return (
    <div className="editable-field">
      {isEditing ? (
        <div className="edit-mode">
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') handleCancel();
            }}
            className="edit-input"
            autoFocus
          />
          <div className="edit-buttons">
            <button onClick={handleSave} className="save-btn">✅</button>
            <button onClick={handleCancel} className="cancel-btn">❌</button>
          </div>
        </div>
      ) : (
        <div className="view-mode" onClick={() => setIsEditing(true)}>
          <span className="field-value">{value || 'N/A'}</span>
          <span className="edit-hint">✏️</span>
        </div>
      )}
    </div>
  );
}

export default App;

