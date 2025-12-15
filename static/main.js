const apiBase = "";

const lineItemsBody = document.getElementById("lineItemsBody");
const totalAmountDisplay = document.getElementById("totalAmountDisplay");
const amountPaidInput = document.getElementById("amountPaid");
const balanceDisplay = document.getElementById("balanceDisplay");
const formError = document.getElementById("formError");
const statusText = document.getElementById("statusText");

const filterDateInput = document.getElementById("filterDate");
const dailyTotalDisplay = document.getElementById("dailyTotalDisplay");
const dailyPaidDisplay = document.getElementById("dailyPaidDisplay");
const historyList = document.getElementById("historyList");

const receiptBackdrop = document.getElementById("receiptBackdrop");
const receiptContent = document.getElementById("receiptContent");
const closeReceiptBtn = document.getElementById("closeReceipt");
const printReceiptBtn = document.getElementById("printReceipt");

const saveButton = document.getElementById("saveButton");
const clearButton = document.getElementById("clearButton");
const addLineButton = document.getElementById("addLineButton");
const refreshHistoryButton = document.getElementById("refreshHistoryButton");

function peso(amount) {
    return "₱" + (amount || 0).toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function setStatus(text, type = "info") {
    statusText.textContent = text || "";
    if (!text) return;
    if (type === "error") {
        statusText.style.color = "#fecaca";
    } else if (type === "success") {
        statusText.style.color = "#bbf7d0";
    } else {
        statusText.style.color = "#a5b4fc";
    }
}

function addLineRow(initial = {}) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>
            <input class="line-input" type="text" placeholder="e.g. Sliding window 2-panel, 4mm clear glass" value="${initial.item_description || ""}">
        </td>
        <td class="qty-col">
            <input class="line-input" type="number" min="0" step="1" value="${initial.quantity || ""}">
        </td>
        <td class="price-col">
            <input class="line-input" type="number" min="0" step="0.01" value="${initial.unit_price || ""}">
        </td>
        <td class="total-col line-total">₱0.00</td>
    `;
    lineItemsBody.appendChild(tr);

    const [descInput, qtyInput, priceInput] = tr.querySelectorAll("input");

    function recalcRow() {
        const qty = Number(qtyInput.value || 0);
        const price = Number(priceInput.value || 0);
        const total = qty * price;
        tr.querySelector(".line-total").textContent = peso(total);
        recalcTotals();
    }

    descInput.addEventListener("input", recalcTotals);
    qtyInput.addEventListener("input", recalcRow);
    priceInput.addEventListener("input", recalcRow);
}

function recalcTotals() {
    let total = 0;
    const rows = lineItemsBody.querySelectorAll("tr");
    rows.forEach((tr) => {
        const inputs = tr.querySelectorAll("input");
        const desc = inputs[0].value.trim();
        const qty = Number(inputs[1].value || 0);
        const price = Number(inputs[2].value || 0);
        if (!desc || qty <= 0 || price < 0) return;
        total += qty * price;
    });

    totalAmountDisplay.textContent = peso(total);

    const paid = Number(amountPaidInput.value || 0);
    const balance = total - paid;
    balanceDisplay.textContent = peso(balance);
    balanceDisplay.classList.toggle("accent", balance <= 0 && total > 0);
    balanceDisplay.classList.toggle("danger", balance > 0 || total === 0);
}

function collectForm() {
    const customerName = document.getElementById("customerName").value.trim();
    const contact = document.getElementById("contact").value.trim();
    const description = document.getElementById("description").value.trim();

    const items = [];
    const rows = lineItemsBody.querySelectorAll("tr");
    rows.forEach((tr) => {
        const inputs = tr.querySelectorAll("input");
        const item_description = inputs[0].value.trim();
        const quantity = Number(inputs[1].value || 0);
        const unit_price = Number(inputs[2].value || 0);
        if (!item_description || quantity <= 0 || unit_price < 0) return;
        items.push({ item_description, quantity, unit_price });
    });

    const amount_paid = Number(amountPaidInput.value || 0);

    return {
        customer_name: customerName,
        contact,
        description,
        items,
        amount_paid,
    };
}

async function saveTransaction() {
    formError.textContent = "";
    const payload = collectForm();

    if (!payload.customer_name) {
        formError.textContent = "Customer name is required.";
        return;
    }
    if (!payload.description) {
        formError.textContent = "Please describe the overall job or project.";
        return;
    }
    if (!payload.items.length) {
        formError.textContent = "Add at least one valid line item (description, quantity, and price).";
        return;
    }

    setStatus("Saving transaction…");
    saveButton.disabled = true;

    try {
        const res = await fetch(apiBase + "/api/transactions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "Failed to save transaction.");
        }

        setStatus("Transaction saved. E-receipt ready.", "success");
        openReceiptModal(data);
        loadHistory();
    } catch (err) {
        console.error(err);
        setStatus("Could not save. Please try again.", "error");
        formError.textContent = err.message || "Something went wrong while saving.";
    } finally {
        saveButton.disabled = false;
    }
}

function clearForm() {
    document.getElementById("customerName").value = "";
    document.getElementById("contact").value = "";
    document.getElementById("description").value = "";
    amountPaidInput.value = 0;
    lineItemsBody.innerHTML = "";
    addLineRow();
    recalcTotals();
    formError.textContent = "";
    setStatus("");
}

function setTodayOnFilter() {
    const today = new Date();
    const iso = today.toISOString().slice(0, 10);
    filterDateInput.value = iso;
}

async function loadHistory() {
    const date = filterDateInput.value;
    try {
        const res = await fetch(apiBase + "/api/transactions" + (date ? "?date=" + date : ""));
        const data = await res.json();

        dailyTotalDisplay.textContent = peso(data.daily_total);
        dailyPaidDisplay.textContent = peso(data.daily_paid);

        historyList.innerHTML = "";
        if (!data.transactions || !data.transactions.length) {
            historyList.innerHTML = '<div class="history-row"><span class="history-meta">No transactions yet for this day.</span></div>';
            return;
        }

        data.transactions.forEach((tx) => {
            const div = document.createElement("div");
            div.className = "history-row";

            const isPaid = tx.balance <= 0.001;

            div.innerHTML = `
                <div class="history-main">
                    <span class="history-customer">${tx.customer_name}</span>
                    <span class="history-meta">
                        #${String(tx.id).padStart(4, "0")} &nbsp;&bull;&nbsp;
                        ${new Date(tx.created_at).toLocaleTimeString("en-PH", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                </div>
                <div class="history-amount">
                    <div>${peso(tx.total_amount)}</div>
                    <div style="font-size:0.7rem;color:${isPaid ? "#bbf7d0" : "#fecaca"};">
                        ${isPaid ? "Paid in full" : "Balance " + peso(tx.balance)}
                    </div>
                </div>
                <div class="history-actions">
                    <span class="chip ${isPaid ? "green" : "red"}">${isPaid ? "Paid" : "With balance"}</span>
                    <button type="button" class="link-button" data-id="${tx.id}">View receipt</button>
                </div>
            `;

            const viewBtn = div.querySelector("button");
            viewBtn.addEventListener("click", () => openReceiptModal(tx));
            historyList.appendChild(div);
        });
    } catch (err) {
        console.error(err);
        historyList.innerHTML = '<div class="history-row"><span class="history-meta">Could not load history.</span></div>';
    }
}

function openReceiptModal(tx) {
    const isPaid = tx.balance <= 0.001;
    const createdDate = new Date(tx.created_at);
    const dateStr = createdDate.toLocaleDateString("en-PH", { year: "numeric", month: "short", day: "numeric" });
    const timeStr = createdDate.toLocaleTimeString("en-PH", { hour: "2-digit", minute: "2-digit" });

    let itemsRows = "";
    if (tx.items && tx.items.length) {
        tx.items.forEach((item, idx) => {
            itemsRows += `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${item.item_description}</td>
                    <td style="text-align:right;">${item.quantity}</td>
                    <td style="text-align:right;">${peso(item.unit_price)}</td>
                    <td style="text-align:right;">${peso(item.line_total)}</td>
                </tr>
            `;
        });
    } else {
        itemsRows = `
            <tr>
                <td colspan="5" style="text-align:center;color:#9ca3af;">No breakdown captured for this job.</td>
            </tr>
        `;
    }

    receiptContent.innerHTML = `
        <div class="receipt-meta">
            <div>
                <div><strong>Customer:</strong> ${tx.customer_name}</div>
                ${tx.contact ? `<div><strong>Contact:</strong> ${tx.contact}</div>` : ""}
            </div>
            <div style="text-align:right;">
                <div><strong>Receipt #</strong> ${String(tx.id).padStart(4, "0")}</div>
                <div>${dateStr} &nbsp; ${timeStr}</div>
            </div>
        </div>
        <div style="font-size:0.78rem;margin:6px 0 4px;">
            <strong>Job / project:</strong><br>
            <span style="color:#e5e7eb;">${tx.description}</span>
        </div>
        <table class="receipt-table">
            <thead>
                <tr>
                    <th style="width:32px;">#</th>
                    <th>Description</th>
                    <th style="width:60px;text-align:right;">Qty</th>
                    <th style="width:80px;text-align:right;">Unit</th>
                    <th style="width:90px;text-align:right;">Total</th>
                </tr>
            </thead>
            <tbody>
                ${itemsRows}
            </tbody>
        </table>
        <div style="margin-top:8px;display:flex;justify-content:flex-end;">
            <table style="font-size:0.8rem;">
                <tr>
                    <td style="padding:2px 8px;color:#9ca3af;">Total amount</td>
                    <td style="padding:2px 0;text-align:right;">${peso(tx.total_amount)}</td>
                </tr>
                <tr>
                    <td style="padding:2px 8px;color:#9ca3af;">Amount paid</td>
                    <td style="padding:2px 0;text-align:right;">${peso(tx.amount_paid)}</td>
                </tr>
                <tr>
                    <td style="padding:2px 8px;color:#9ca3af;">Balance</td>
                    <td style="padding:2px 0;text-align:right;color:${isPaid ? "#bbf7d0" : "#fecaca"};">${peso(tx.balance)}</td>
                </tr>
            </table>
        </div>
        <div class="receipt-footer">
            <span>Status: <strong style="color:${isPaid ? "#bbf7d0" : "#fecaca"};">${isPaid ? "PAID" : "WITH BALANCE"}</strong></span>
            <span>Thank you for trusting Salay Glass.</span>
        </div>
    `;

    receiptBackdrop.style.display = "flex";
}

function closeReceiptModal() {
    receiptBackdrop.style.display = "none";
}

function printCurrentReceipt() {
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;

    printWindow.document.write(`
        <html>
        <head>
            <title>Salay Glass E-Receipt</title>
            <style>
                body {
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    padding: 18px;
                    color: #111827;
                }
                h2 {
                    text-transform: uppercase;
                    letter-spacing: 0.12em;
                    font-size: 1rem;
                    margin-bottom: 2px;
                }
                .muted { font-size: 0.78rem; color: #6b7280; }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    font-size: 0.8rem;
                }
                th, td { padding: 5px 4px; }
                th {
                    border-bottom: 1px solid #9ca3af;
                    font-size: 0.72rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: #6b7280;
                }
                td {
                    border-bottom: 1px dashed #d1d5db;
                }
                .right { text-align: right; }
                .footer {
                    margin-top: 14px;
                    font-size: 0.76rem;
                    color: #6b7280;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
            </style>
        </head>
        <body>
            <h2>Salay Glass</h2>
            <div class="muted">Glass & aluminum fabrication and installation &mdash; E-Receipt</div>
            ${receiptContent.innerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
}

// Event wiring
addLineButton.addEventListener("click", () => addLineRow());
saveButton.addEventListener("click", saveTransaction);
clearButton.addEventListener("click", clearForm);
amountPaidInput.addEventListener("input", recalcTotals);
filterDateInput.addEventListener("change", loadHistory);
refreshHistoryButton.addEventListener("click", loadHistory);
closeReceiptBtn.addEventListener("click", closeReceiptModal);
printReceiptBtn.addEventListener("click", printCurrentReceipt);
receiptBackdrop.addEventListener("click", (e) => {
    if (e.target === receiptBackdrop) closeReceiptModal();
});

// Initial setup
addLineRow();
addLineRow();
setTodayOnFilter();
recalcTotals();
loadHistory();
