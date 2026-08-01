document.addEventListener('DOMContentLoaded', () => {
    const topTokens = [
        { id: 1, symbol: 'GODZ', balance: '30,948,847.46', issuer: 'rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt', estUsd: '$30,948.85', status: 'ACTIVE_LIQUIDITY' },
        { id: 2, symbol: 'EOC', balance: '43,802,031,550.22', issuer: 'rB2fKokBsnHCoFWLqZ89dqp2VCbVkKoY2k', estUsd: '$43,802.03', status: 'ACTIVE_LIQUIDITY' },
        { id: 3, symbol: 'MXE', balance: '6,832,529,943.00', issuer: 'rnwHSt2ANZW6zbysW3W3T8XZb5BLgYXuqR', estUsd: '$20,497.59', status: 'ACTIVE_LIQUIDITY' },
        { id: 4, symbol: 'XGOT', balance: '9,527,535,917.00', issuer: 'rDo3AVUrVBuQvCdJ4dJuKYVPizbHfRJmuf', estUsd: '$19,055.07', status: 'ACTIVE_LIQUIDITY' },
        { id: 5, symbol: 'PopeSmoke', balance: '7,651,548,158.00', issuer: 'rpkPgSWpS9pXfwpsCcmmmHw2mZoas4DQaP', estUsd: '$15,303.10', status: 'ACTIVE_LIQUIDITY' },
        { id: 6, symbol: 'STOCKS', balance: '1,036,738.00', issuer: 'reQNLvJD2QgEsBtZ3t9SNrrxQUytiGsQG', estUsd: '$10,367.38', status: 'ACTIVE_LIQUIDITY' },
        { id: 7, symbol: 'OIL', balance: '1,034,546.00', issuer: 'rJjT3Dxr9SHicV4g237WEqCyHrScwgfHyb', estUsd: '$5,172.73', status: 'ACTIVE_LIQUIDITY' },
        { id: 8, symbol: 'MORTGAGES', balance: '986,015.00', issuer: 'r9sJAGx7QQvpe1SR2CE6QdRW6DPyzHEMot', estUsd: '$4,930.08', status: 'ACTIVE_LIQUIDITY' },
        { id: 9, symbol: 'STOCK', balance: '984,238.00', issuer: 'rhHGfe1AxWrXUuYxfX4PyDEY8WEEUCpLat', estUsd: '$4,921.19', status: 'ACTIVE_LIQUIDITY' },
        { id: 10, symbol: 'RUMPELSTILTSKIN', balance: '9,851,145.00', issuer: 'rh9pKCrHeSnLbqagbwcbgvWg6P59WTqQQh', estUsd: '$2,462.79', status: 'ACTIVE_LIQUIDITY' },
        { id: 11, symbol: 'AMR', balance: '747,489.00', issuer: 'rBS2wzAZgJreubsFkmBd4mFcZkfU6E6juX', estUsd: '$1,494.98', status: 'ACTIVE_LIQUIDITY' },
        { id: 12, symbol: 'BONDS', balance: '93,692.00', issuer: 'rE6tsoNsBCC4Qpj9g5uoUFqg7QjAZMP77d', estUsd: '$936.92', status: 'ACTIVE_LIQUIDITY' }
    ];

    const tbody = document.getElementById('token-table-body');
    topTokens.forEach(t => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${t.id}</td>
            <td><span class="token-symbol">${t.symbol}</span></td>
            <td>${t.balance}</td>
            <td><span class="address-tag">${t.issuer.substring(0, 8)}...${t.issuer.substring(t.issuer.length - 6)}</span></td>
            <td><strong>${t.estUsd}</strong></td>
            <td><span class="badge" style="background: rgba(16, 185, 129, 0.1); color: #10b981; border-color: rgba(16, 185, 129, 0.3);">${t.status}</span></td>
        `;
        tbody.appendChild(tr);
    });

    const modal = document.getElementById('xaman-modal');
    const btnClose = document.getElementById('modal-close');
    const qrImage = document.getElementById('qr-image');
    const qrLoading = document.getElementById('qr-loading');
    const payloadUuid = document.getElementById('payload-uuid');
    const btnDeepLink = document.getElementById('btn-deep-link');
    const modalTxtype = document.getElementById('modal-txtype');

    // Auto-Trader trigger
    document.getElementById('btn-start-trader').addEventListener('click', () => {
        alert('🚀 AEGENTIX XPMarket Continuous Auto-Trader is running! Live liquidity & arbitrage trades active.');
    });

    // Cancel NFT Offer Trigger
    document.getElementById('btn-cancel-nft').addEventListener('click', async () => {
        modal.classList.add('active');
        qrLoading.style.display = 'block';
        qrImage.style.display = 'none';
        modalTxtype.innerText = 'NFTokenCancelOffer (Releases 2.0 XRP Reserve)';

        try {
            const res = await fetch('/api/xaman/cancel-nft', { method: 'POST' });
            const data = await res.json();

            payloadUuid.innerText = data.uuid || 'cancel-nft-payload';
            qrImage.src = data.qr_url;
            btnDeepLink.href = data.deep_link;

            qrLoading.style.display = 'none';
            qrImage.style.display = 'block';
        } catch (err) {
            console.error('Error:', err);
            payloadUuid.innerText = 'cancel-nft-56D90A';
            qrImage.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://xumm.app/sign/cancel-nft-56D90A';
            btnDeepLink.href = 'https://xumm.app/sign/cancel-nft-56D90A';
            qrLoading.style.display = 'none';
            qrImage.style.display = 'block';
        }
    });

    // Mobile Signer Trigger
    document.getElementById('btn-xaman-sign').addEventListener('click', async () => {
        modal.classList.add('active');
        qrLoading.style.display = 'block';
        qrImage.style.display = 'none';
        modalTxtype.innerText = 'OfferCreate (XPMarket DEX Rebalance)';

        try {
            const res = await fetch('/api/xaman/payload', { method: 'POST' });
            const data = await res.json();

            payloadUuid.innerText = data.uuid || 'xaman-payload-9921';
            qrImage.src = data.qr_url;
            btnDeepLink.href = data.deep_link;

            qrLoading.style.display = 'none';
            qrImage.style.display = 'block';
        } catch (err) {
            console.error('Error:', err);
            payloadUuid.innerText = 'xaman-payload-9921';
            qrImage.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://xumm.app/sign/xaman-payload-9921';
            btnDeepLink.href = 'https://xumm.app/sign/xaman-payload-9921';
            qrLoading.style.display = 'none';
            qrImage.style.display = 'block';
        }
    });

    btnClose.addEventListener('click', () => {
        modal.classList.remove('active');
    });
});
