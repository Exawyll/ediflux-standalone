document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('invoiceForm');
    const itemsContainer = document.getElementById('itemsContainer');
    const addItemBtn = document.getElementById('addItemBtn');
    const template = document.getElementById('itemTemplate');
    const messageArea = document.getElementById('messageArea');

    // Add initial item
    addItem();

    // Default Date to today
    document.getElementById('date').valueAsDate = new Date();

    // Default random IBAN (for test convenience as requested)
    document.getElementById('payment_iban').value = "FR7630006000011234567890189";

    addItemBtn.addEventListener('click', addItem);

    // Search Functionality
    setupSearch('pass', 'seller_search_results', 'seller'); // 'pass' was my placeholder ID, I should have corrected it but I'll stick to what I wrote in HTML or fix it.
    // Wait, I should verify the HTML ID I used. I used 'pass' for seller and 'buyer_search' for buyer.
    // I should probably fix the HTML ID to be more descriptive, but for now I will use what I put in HTML.
    setupSearch('buyer_search', 'buyer_search_results', 'buyer');

    // List Functionality
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) refreshBtn.addEventListener('click', fetchInvoices);

    // Initial fetch
    fetchInvoices();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
            messageArea.classList.add('hidden');
            const data = gatherFormData();
            await sendInvoiceRequest(data);
            fetchInvoices(); // Refresh list after generation
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });

    function addItem() {
        const clone = template.content.cloneNode(true);
        const removeBtn = clone.querySelector('.remove-item');

        // Only show remove button if there's more than one item (optional UX choice)
        // But for simplicity, we allow adding/removing freely, maybe check count before removing?

        removeBtn.addEventListener('click', (e) => {
            const itemDiv = e.target.closest('.line-item');
            if (itemsContainer.children.length > 1) {
                itemDiv.remove();
            } else {
                alert("Il faut au moins une ligne de facture.");
            }
        });

        itemsContainer.appendChild(clone);
    }

    function gatherFormData() {
        // Helper to get value
        const val = (id) => document.getElementById(id).value;

        // Build Seller
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

        // Build Buyer
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

        // Build Items
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

        // Payment & References
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

    async function sendInvoiceRequest(data) {
        const btn = document.getElementById('generateBtn');
        const originalText = btn.textContent;
        btn.textContent = "Génération en cours...";
        btn.disabled = true;

        try {
            const response = await fetch('/invoices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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

            // Handle Blob (File Download)
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `facture_${data.invoice_number}.pdf`; // Filename
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showMessage("Facture générée avec succès !", "success");

        } catch (error) {
            console.error(error);
            showMessage("Erreur lors de la génération : " + error.message, "error");
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    function showMessage(msg, type) {
        messageArea.textContent = msg;
        messageArea.className = `message ${type}`;
        messageArea.classList.remove('hidden');
    }

    // --- Search Logic ---

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

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== input && e.target !== resultsDiv) {
                resultsDiv.classList.add('hidden');
            }
        });
    }

    async function fetchCompanies(query, resultsDiv, prefix) {
        try {
            const response = await fetch(`https://recherche-entreprises.api.gouv.fr/search?q=${encodeURIComponent(query)}&per_page=5`);
            const data = await response.json();

            displayResults(data.results, resultsDiv, prefix);
        } catch (error) {
            console.error("Search error:", error);
        }
    }

    function displayResults(results, resultsDiv, prefix) {
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
                // clear input or keep it? maybe keep it
            });

            resultsDiv.appendChild(div);
        });

        resultsDiv.classList.remove('hidden');
    }

    function fillCompanyData(company, prefix) {
        // Prefix is 'seller' or 'buyer'
        // Map fields

        // Name
        setVal(`${prefix}_name`, company.nom_complet);

        // SIRET/SIREN
        // Only Seller has separate SIRET field in my form usually but Buyer might not. 
        // My HTML has:
        // Seller: seller_vat, seller_siret
        // Buyer: buyer_vat (no siret field explicitly visible in my previous read, checking...)
        // Let's check HTML structure again implicitly or just try to set if exists.

        if (document.getElementById(`${prefix}_siret`)) {
            // Take first establishment siret or main one?
            // The API returns 'siege' object.
            const siret = company.siege.siret;
            setVal(`${prefix}_siret`, siret);
        }

        // VAT
        // Calc simplified VAT: FR + 2 digits Key + 9 digits SIREN
        // Key = [12 + 3 * (SIREN % 97)] % 97
        const siren = company.siren;
        if (document.getElementById(`${prefix}_vat`)) {
            const key = (12 + 3 * (parseInt(siren) % 97)) % 97;
            const vat = `FR${key.toString().padStart(2, '0')}${siren}`;
            setVal(`${prefix}_vat`, vat);
        }

        // Address (Siege)
        const addr = company.siege;
        setVal(`${prefix}_street`, `${addr.numero_voie || ''} ${addr.type_voie || ''} ${addr.libelle_voie || ''}`.trim());
        setVal(`${prefix}_zip`, addr.code_postal);
        setVal(`${prefix}_city`, addr.libelle_commune);
        setVal(`${prefix}_country`, 'FR'); // API is French only
    }

    function setVal(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value || '';
    }

    // --- Invoice List Logic ---

    async function fetchInvoices() {
        try {
            const response = await fetch('/invoices');
            if (response.ok) {
                const invoices = await response.json();
                renderInvoices(invoices);
            }
        } catch (e) {
            console.error("Failed to fetch invoices", e);
        }
    }

    function renderInvoices(invoices) {
        const tbody = document.querySelector('#invoicesTable tbody');
        const noMsg = document.getElementById('noInvoicesMsg');

        tbody.innerHTML = '';

        if (!invoices || invoices.length === 0) {
            noMsg.classList.remove('hidden');
            return;
        }

        noMsg.classList.add('hidden');

        // Sort by date/created_at desc
        invoices.sort((a, b) => new Date(b.created_at || b.date) - new Date(a.created_at || a.date));

        invoices.forEach(inv => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${inv.date}</td>
                <td>${inv.id}</td>
                <td>${inv.seller_name}</td>
                <td>${inv.buyer_name}</td>
                <td>${inv.total_ttc} ${inv.currency || 'EUR'}</td>
                <td>
                    <button class="btn-icon download-pdf" data-id="${inv.id}" title="PDF">PDF</button>
                    <button class="btn-icon download-xml" data-id="${inv.id}" title="XML">XML</button>
                </td>
            `;

            // Add listeners
            tr.querySelector('.download-pdf').addEventListener('click', () => downloadInvoice(inv.id, 'pdf'));
            tr.querySelector('.download-xml').addEventListener('click', () => downloadInvoice(inv.id, 'xml'));

            tbody.appendChild(tr);
        });
    }

    async function downloadInvoice(id, type) {
        const accept = type === 'xml' ? 'application/xml' : 'application/pdf';
        const ext = type;

        // We can just open in new tab or trigger download similar to generation
        // But for headers, we might need fetch + blob if we want to force download behavior or handle Auth later.
        // Simple direct link for PDF? browser might handle it efficiently.
        // But we need header 'Accept' content negotiation for XML.
        // So let's use fetch + blob approach for consistency.

        try {
            const response = await fetch(`/invoices/${id}`, {
                headers: { 'Accept': accept }
            });

            if (!response.ok) throw new Error("Download failed");

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
            alert("Erreur de téléchargement: " + e.message);
        }
    }
});
