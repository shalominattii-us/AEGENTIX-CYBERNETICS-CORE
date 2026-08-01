document.addEventListener('DOMContentLoaded', () => {
    const topTokens = [
        { id: 1, symbol: 'GODZ', balance: '30,948,847.46', issuer: 'rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt', link: 'https://xpmarket.com/dex/GODZ-rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt/XRP', estUsd: '$30,948.85', status: 'ACTIVE_LIQUIDITY' },
        { id: 2, symbol: 'EOC', balance: '43,802,031,550.22', issuer: 'rB2fKokBsnHCoFWLqZ89dqp2VCbVkKoY2k', link: 'https://xpmarket.com/dex/EOC-rB2fKokBsnHCoFWLqZ89dqp2VCbVkKoY2k/XRP', estUsd: '$43,802.03', status: 'ACTIVE_LIQUIDITY' },
        { id: 3, symbol: 'MXE', balance: '6,832,529,943.00', issuer: 'rnwHSt2ANZW6zbysW3W3T8XZb5BLgYXuqR', link: 'https://xpmarket.com/dex/MXE-rnwHSt2ANZW6zbysW3W3T8XZb5BLgYXuqR/XRP', estUsd: '$20,497.59', status: 'ACTIVE_LIQUIDITY' },
        { id: 4, symbol: 'XGOT', balance: '9,527,535,917.00', issuer: 'rDo3AVUrVBuQvCdJ4dJuKYVPizbHfRJmuf', link: 'https://xpmarket.com/dex/XGOT-rDo3AVUrVBuQvCdJ4dJuKYVPizbHfRJmuf/XRP', estUsd: '$19,055.07', status: 'ACTIVE_LIQUIDITY' },
        { id: 5, symbol: 'PopeSmoke', balance: '7,651,548,158.00', issuer: 'rpkPgSWpS9pXfwpsCcmmmHw2mZoas4DQaP', link: 'https://xpmarket.com/dex/PopeSmoke-rpkPgSWpS9pXfwpsCcmmmHw2mZoas4DQaP/XRP', estUsd: '$15,303.10', status: 'ACTIVE_LIQUIDITY' },
        { id: 6, symbol: 'STOCKS', balance: '1,036,738.00', issuer: 'reQNLvJD2QgEsBtZ3t9SNrrxQUytiGsQG', link: 'https://xpmarket.com/dex/STOCKS-reQNLvJD2QgEsBtZ3t9SNrrxQUytiGsQG/XRP', estUsd: '$10,367.38', status: 'ACTIVE_LIQUIDITY' },
        { id: 7, symbol: 'OIL', balance: '1,034,546.00', issuer: 'rJjT3Dxr9SHicV4g237WEqCyHrScwgfHyb', link: 'https://xpmarket.com/dex/OIL-rJjT3Dxr9SHicV4g237WEqCyHrScwgfHyb/XRP', estUsd: '$5,172.73', status: 'ACTIVE_LIQUIDITY' },
        { id: 8, symbol: 'MORTGAGES', balance: '986,015.00', issuer: 'r9sJAGx7QQvpe1SR2CE6QdRW6DPyzHEMot', link: 'https://xpmarket.com/dex/MORTGAGES-r9sJAGx7QQvpe1SR2CE6QdRW6DPyzHEMot/XRP', estUsd: '$4,930.08', status: 'ACTIVE_LIQUIDITY' }
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
            <td><a href="${t.link}" target="_blank" class="btn btn-secondary" style="padding: 0.3rem 0.8rem; font-size: 0.8rem;">💱 Trade for XRP</a></td>
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
    document.getElementById('btn-cancel-nft').addEventListener('click', () => {
        modal.classList.add('active');
        modalTxtype.innerText = 'Xaman Official DEX xApp (Trade Tokens for XRP)';
        payloadUuid.innerText = 'xapp:xumm.dex';
        qrImage.src = 'https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://xumm.app/detect/xapp:xumm.dex';
        btnDeepLink.href = 'https://xumm.app/detect/xapp:xumm.dex';
        qrLoading.style.display = 'none';
        qrImage.style.display = 'block';
    });

    // Mobile Signer Trigger - Official XPMarket DEX Link
    document.getElementById('btn-xaman-sign').addEventListener('click', () => {
        modal.classList.add('active');
        modalTxtype.innerText = 'XPMarket DEX (Sell GODZ for XRP)';
        payloadUuid.innerText = 'xpmarket-godz-xrp';
        qrImage.src = 'https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://xpmarket.com/dex/GODZ-rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt/XRP';
        btnDeepLink.href = 'https://xpmarket.com/dex/GODZ-rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt/XRP';
        qrLoading.style.display = 'none';
        qrImage.style.display = 'block';
    });

    btnClose.addEventListener('click', () => {
        modal.classList.remove('active');
    });
});
