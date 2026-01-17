document.addEventListener('DOMContentLoaded', () => {
    // ===== DOM Elements =====
    const formView = document.getElementById('formView');
    const detailView = document.getElementById('detailView');
    const invoiceForm = document.getElementById('invoiceForm');
    const itemsContainer = document.getElementById('itemsContainer');
    const addItemBtn = document.getElementById('addItemBtn');
    const template = document.getElementById('itemTemplate');
    const messageArea = document.getElementById('messageArea');
    const invoiceList = document.getElementById('invoiceList');
    const noInvoicesMsg = document.getElementById('noInvoicesMsg');
    const invoiceDetail = document.getElementById('invoiceDetail');

    // Buttons
    const newInvoiceBtn = document.getElementById('newInvoiceBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const backToListBtn = document.getElementById('backToListBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const downloadXmlBtn = document.getElementById('downloadXmlBtn');
    const sendInvoiceBtn = document.getElementById('sendInvoiceBtn');
    const deleteInvoiceBtn = document.getElementById('deleteInvoiceBtn');
    const generateBtn = document.getElementById('generateBtn');

    // Upload elements
    const modeToggleBtns = document.querySelectorAll('.mode-btn');
    const uploadSection = document.getElementById('uploadSection');
    const uploadDropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadMessageArea = document.getElementById('uploadMessageArea');

    // State
    let currentInvoiceId = null;
    let invoicesData = [];
    let selectedFile = null;
    let currentMode = 'create';

    // ===== Initialization =====
    addItem();
    document.getElementById('date').valueAsDate = new Date();
    document.getElementById('payment_iban').value = "FR7630006000011234567890189";

    // Setup event listeners
    addItemBtn.addEventListener('click', addItem);
    newInvoiceBtn.addEventListener('click', showFormView);
    refreshBtn.addEventListener('click', fetchInvoices);
    backToListBtn.addEventListener('click', showFormView);
    downloadPdfBtn.addEventListener('click', () => downloadInvoice(currentInvoiceId, 'pdf'));
    downloadXmlBtn.addEventListener('click', () => downloadInvoice(currentInvoiceId, 'xml'));
    sendInvoiceBtn.addEventListener('click', () => sendInvoice(currentInvoiceId));
    deleteInvoiceBtn.addEventListener('click', () => deleteInvoice(currentInvoiceId));

    // Setup company search
    setupSearch('seller_search', 'seller_search_results', 'seller');
    setupSearch('buyer_search', 'buyer_search_results', 'buyer');

    // Setup collapsible sections
    setupCollapsibleSections();

    // Setup upload functionality
    setupUpload();

    // Initial fetch
    fetchInvoices();

    // Form submission
    invoiceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            messageArea.classList.add('hidden');
            const data = gatherFormData();
            await sendInvoiceRequest(data);
            fetchInvoices();
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });

    // ===== View Management =====
    function showFormView() {
        formView.classList.add('active');
        detailView.classList.remove('active');
        currentInvoiceId = null;
        updateActiveInvoiceInList(null);
    }

    function showDetailView(invoiceId) {
        const invoice = invoicesData.find(inv => inv.id === invoiceId);
        if (!invoice) return;

        currentInvoiceId = invoiceId;
        renderInvoiceDetail(invoice);
        formView.classList.remove('active');
        detailView.classList.add('active');
        updateActiveInvoiceInList(invoiceId);
    }

    function updateActiveInvoiceInList(activeId) {
        document.querySelectorAll('.invoice-list-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === activeId);
        });
    }

    // ===== Collapsible Sections =====
    function setupCollapsibleSections() {
        document.querySelectorAll('.section-header').forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.form-section');
                section.classList.toggle('collapsed');
            });
        });
    }

    // ===== Upload Functionality =====
    function setupUpload() {
        // Mode toggle
        modeToggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                switchMode(mode);
            });
        });

        // Dropzone click to select file
        uploadDropzone.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
            }
        });

        // Drag & drop events
        uploadDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.add('dragover');
        });

        uploadDropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.remove('dragover');
        });

        uploadDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.remove('dragover');

            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        // Remove file button
        removeFileBtn.addEventListener('click', () => {
            clearSelectedFile();
        });

        // Upload button
        uploadBtn.addEventListener('click', () => {
            uploadFile();
        });
    }

    function switchMode(mode) {
        currentMode = mode;

        // Update toggle buttons
        modeToggleBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Show/hide sections
        if (mode === 'upload') {
            uploadSection.classList.remove('hidden');
            invoiceForm.classList.add('hidden');
        } else {
            uploadSection.classList.add('hidden');
            invoiceForm.classList.remove('hidden');
        }

        // Clear any messages
        uploadMessageArea.classList.add('hidden');
        messageArea.classList.add('hidden');
    }

    function handleFileSelect(file) {
        // Validate file type
        const ext = file.name.toLowerCase().split('.').pop();
        if (ext !== 'pdf' && ext !== 'xml') {
            showUploadMessage('Type de fichier invalide. Formats acceptes: PDF, XML', 'error');
            return;
        }

        selectedFile = file;

        // Update preview
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);

        // Show preview, hide dropzone
        uploadDropzone.classList.add('hidden');
        filePreview.classList.remove('hidden');

        // Enable upload button
        uploadBtn.disabled = false;

        // Clear any previous error messages
        uploadMessageArea.classList.add('hidden');
    }

    function clearSelectedFile() {
        selectedFile = null;
        fileInput.value = '';

        // Hide preview, show dropzone
        filePreview.classList.add('hidden');
        uploadDropzone.classList.remove('hidden');

        // Disable upload button
        uploadBtn.disabled = true;
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' octets';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
        return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
    }

    function showUploadMessage(msg, type) {
        uploadMessageArea.textContent = msg;
        uploadMessageArea.className = `message ${type}`;
        uploadMessageArea.classList.remove('hidden');

        if (type === 'success') {
            setTimeout(() => {
                uploadMessageArea.classList.add('hidden');
            }, 5000);
        }
    }

    async function uploadFile() {
        if (!selectedFile) return;

        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = `
            <svg class="spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56"></path>
            </svg>
            Import en cours...
        `;
        uploadBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const response = await fetch('/invoices/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Erreur ${response.status}`);
            }

            const metadata = await response.json();
            showUploadMessage(`Facture ${metadata.id} importee avec succes !`, 'success');

            // Clear the file and refresh the list
            clearSelectedFile();
            fetchInvoices();

            // Optionally show the imported invoice
            setTimeout(() => {
                showDetailView(metadata.id);
            }, 500);

        } catch (error) {
            console.error('Upload error:', error);
            showUploadMessage('Erreur lors de l\'import: ' + error.message, 'error');
        } finally {
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = selectedFile === null;
        }
    }

    // ===== Line Items =====
    function addItem() {
        const clone = template.content.cloneNode(true);
        const removeBtn = clone.querySelector('.btn-remove-item');

        removeBtn.addEventListener('click', (e) => {
            const itemDiv = e.target.closest('.line-item');
            if (itemsContainer.children.length > 1) {
                itemDiv.remove();
            } else {
                showMessage("Une facture doit avoir au moins une ligne.", 'error');
            }
        });

        itemsContainer.appendChild(clone);
    }

    // ===== Form Data =====
    function gatherFormData() {
        const val = (id) => document.getElementById(id).value;

        const seller = {
            name: val('seller_name'),
            address: {
                street: val('seller_street'),
                zip_code: val('seller_zip'),
                city: val('seller_city'),
                country_code: val('seller_country')
            },
            vat_id: val('seller_vat') || null,
            siret: val('seller_siret') || null,
            email: val('seller_email') || null
        };

        const buyer = {
            name: val('buyer_name'),
            address: {
                street: val('buyer_street'),
                zip_code: val('buyer_zip'),
                city: val('buyer_city'),
                country_code: val('buyer_country')
            },
            vat_id: val('buyer_vat') || null
        };

        const items = [];
        const itemDivs = itemsContainer.querySelectorAll('.line-item');
        itemDivs.forEach(div => {
            items.push({
                description: div.querySelector('.item-desc').value,
                quantity: parseFloat(div.querySelector('.item-qty').value),
                unit_price: parseFloat(div.querySelector('.item-price').value),
                vat_rate: parseFloat(div.querySelector('.item-vat').value)
            });
        });

        const payment = {
            iban: val('payment_iban') || null,
            mode: val('payment_mode')
        };

        const references = {
            buyer_reference: val('ref_buyer') || null,
            order_reference: val('ref_order') || null
        };

        return {
            invoice_number: val('invoice_number'),
            date: val('date'),
            seller: seller,
            buyer: buyer,
            items: items,
            payment: payment,
            references: references,
            currency: "EUR"
        };
    }

    // ===== API Calls =====
    async function sendInvoiceRequest(data) {
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = `
            <svg class="spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56"></path>
            </svg>
            Generation...
        `;
        generateBtn.disabled = true;

        try {
            const response = await fetch('/invoices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errText = await response.text();
                let errMessage = `Erreur ${response.status}: ${response.statusText}`;
                try {
                    const errJson = JSON.parse(errText);
                    if (errJson.detail) errMessage += ` - ${errJson.detail}`;
                } catch (e) { }
                throw new Error(errMessage);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `facture_${data.invoice_number}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showMessage("Facture generee avec succes !", "success");
        } catch (error) {
            console.error(error);
            showMessage("Erreur lors de la generation : " + error.message, "error");
        } finally {
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    }

    async function fetchInvoices() {
        try {
            const response = await fetch('/invoices');
            if (response.ok) {
                invoicesData = await response.json();
                renderInvoiceList(invoicesData);
            }
        } catch (e) {
            console.error("Failed to fetch invoices", e);
        }
    }

    async function downloadInvoice(id, type) {
        const accept = type === 'xml' ? 'application/xml' : 'application/pdf';
        const ext = type;

        try {
            const response = await fetch(`/invoices/${id}`, {
                headers: { 'Accept': accept }
            });

            if (!response.ok) throw new Error("Echec du telechargement");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `facture_${id}.${ext}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (e) {
            showMessage("Erreur de telechargement: " + e.message, 'error');
        }
    }

    async function sendInvoice(id) {
        const originalText = sendInvoiceBtn.innerHTML;
        sendInvoiceBtn.innerHTML = `
            <svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56"></path>
            </svg>
            Envoi...
        `;
        sendInvoiceBtn.disabled = true;

        try {
            const response = await fetch(`/invoices/${id}/send`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Erreur lors de l'envoi");
            }

            showMessage("Facture envoyee avec succes !", "success");
        } catch (e) {
            showMessage("Erreur d'envoi: " + e.message, 'error');
        } finally {
            sendInvoiceBtn.innerHTML = originalText;
            sendInvoiceBtn.disabled = false;
        }
    }

    async function deleteInvoice(id) {
        if (!confirm(`Etes-vous sur de vouloir supprimer la facture ${id} ?`)) {
            return;
        }

        const originalText = deleteInvoiceBtn.innerHTML;
        deleteInvoiceBtn.innerHTML = `
            <svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56"></path>
            </svg>
            Suppression...
        `;
        deleteInvoiceBtn.disabled = true;

        try {
            const response = await fetch(`/invoices/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errText = await response.text();
                let errMessage = "Erreur lors de la suppression";
                try {
                    const errData = JSON.parse(errText);
                    if (errData.detail) errMessage = errData.detail;
                } catch (e) { }
                throw new Error(errMessage);
            }

            showMessage("Facture supprimee avec succes !", "success");
            showFormView();
            fetchInvoices();
        } catch (e) {
            showMessage("Erreur de suppression: " + e.message, 'error');
        } finally {
            deleteInvoiceBtn.innerHTML = originalText;
            deleteInvoiceBtn.disabled = false;
        }
    }

    // ===== Rendering =====
    function renderInvoiceList(invoices) {
        invoiceList.innerHTML = '';

        if (!invoices || invoices.length === 0) {
            noInvoicesMsg.classList.remove('hidden');
            return;
        }

        noInvoicesMsg.classList.add('hidden');

        // Sort by date descending
        invoices.sort((a, b) => new Date(b.created_at || b.date) - new Date(a.created_at || a.date));

        invoices.forEach(inv => {
            const item = document.createElement('div');
            item.className = 'invoice-list-item';
            item.dataset.id = inv.id;

            if (inv.id === currentInvoiceId) {
                item.classList.add('active');
            }

            const formattedDate = formatDate(inv.date);
            const formattedAmount = formatCurrency(inv.total_ttc, inv.currency);

            item.innerHTML = `
                <div class="invoice-id">${escapeHtml(inv.id)}</div>
                <div class="invoice-meta">
                    <span>${formattedDate}</span>
                    <span class="invoice-amount">${formattedAmount}</span>
                </div>
            `;

            item.addEventListener('click', () => showDetailView(inv.id));
            invoiceList.appendChild(item);
        });
    }

    function renderInvoiceDetail(invoice) {
        const formattedDate = formatDate(invoice.date);
        const totalHT = invoice.total_ht || 0;
        const totalTTC = invoice.total_ttc || 0;
        const tva = totalTTC - totalHT;
        const currency = invoice.currency || 'EUR';

        invoiceDetail.innerHTML = `
            <div class="detail-header">
                <div class="invoice-number">${escapeHtml(invoice.id)}</div>
                <div class="invoice-date">Date: ${formattedDate}</div>
            </div>
            <div class="detail-body">
                <div class="detail-grid">
                    <div class="detail-section">
                        <h4>Vendeur</h4>
                        <div class="company-name">${escapeHtml(invoice.seller_name)}</div>
                        <div class="address">
                            ${invoice.seller_address ? escapeHtml(invoice.seller_address) : ''}
                        </div>
                        ${invoice.seller_vat ? `<div class="tax-id">TVA: ${escapeHtml(invoice.seller_vat)}</div>` : ''}
                    </div>
                    <div class="detail-section">
                        <h4>Acheteur</h4>
                        <div class="company-name">${escapeHtml(invoice.buyer_name)}</div>
                        <div class="address">
                            ${invoice.buyer_address ? escapeHtml(invoice.buyer_address) : ''}
                        </div>
                        ${invoice.buyer_vat ? `<div class="tax-id">TVA: ${escapeHtml(invoice.buyer_vat)}</div>` : ''}
                    </div>
                </div>

                <div class="detail-totals">
                    <div class="total-row">
                        <span class="label">Total HT</span>
                        <span class="value">${formatCurrency(totalHT, currency)}</span>
                    </div>
                    <div class="total-row">
                        <span class="label">TVA</span>
                        <span class="value">${formatCurrency(tva, currency)}</span>
                    </div>
                    <div class="total-row grand-total">
                        <span class="label">Total TTC</span>
                        <span class="value">${formatCurrency(totalTTC, currency)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // ===== Search =====
    function setupSearch(inputId, resultsId, prefix) {
        const input = document.getElementById(inputId);
        const resultsDiv = document.getElementById(resultsId);
        let debounceTimer;

        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();

            if (query.length < 3) {
                resultsDiv.classList.add('hidden');
                return;
            }

            debounceTimer = setTimeout(() => {
                fetchCompanies(query, resultsDiv, prefix);
            }, 300);
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-wrapper')) {
                resultsDiv.classList.add('hidden');
            }
        });
    }

    async function fetchCompanies(query, resultsDiv, prefix) {
        try {
            const response = await fetch(`https://recherche-entreprises.api.gouv.fr/search?q=${encodeURIComponent(query)}&per_page=5`);
            const data = await response.json();
            displaySearchResults(data.results, resultsDiv, prefix);
        } catch (error) {
            console.error("Search error:", error);
        }
    }

    function displaySearchResults(results, resultsDiv, prefix) {
        resultsDiv.innerHTML = '';
        if (!results || results.length === 0) {
            resultsDiv.classList.add('hidden');
            return;
        }

        results.forEach(company => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.textContent = `${company.nom_complet} (${company.siren})`;

            div.addEventListener('click', () => {
                fillCompanyData(company, prefix);
                resultsDiv.classList.add('hidden');
            });

            resultsDiv.appendChild(div);
        });

        resultsDiv.classList.remove('hidden');
    }

    function fillCompanyData(company, prefix) {
        setVal(`${prefix}_name`, company.nom_complet);

        if (document.getElementById(`${prefix}_siret`)) {
            const siret = company.siege.siret;
            setVal(`${prefix}_siret`, siret);
        }

        const siren = company.siren;
        if (document.getElementById(`${prefix}_vat`)) {
            const key = (12 + 3 * (parseInt(siren) % 97)) % 97;
            const vat = `FR${key.toString().padStart(2, '0')}${siren}`;
            setVal(`${prefix}_vat`, vat);
        }

        const addr = company.siege;
        setVal(`${prefix}_street`, `${addr.numero_voie || ''} ${addr.type_voie || ''} ${addr.libelle_voie || ''}`.trim());
        setVal(`${prefix}_zip`, addr.code_postal);
        setVal(`${prefix}_city`, addr.libelle_commune);
        setVal(`${prefix}_country`, 'FR');
    }

    // ===== Utilities =====
    function setVal(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value || '';
    }

    function showMessage(msg, type) {
        messageArea.textContent = msg;
        messageArea.className = `message ${type}`;
        messageArea.classList.remove('hidden');

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                messageArea.classList.add('hidden');
            }, 5000);
        }
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    function formatCurrency(amount, currency = 'EUR') {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency
        }).format(amount || 0);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});

// Add CSS for spin animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .spin {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
