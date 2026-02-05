/* =========================================
   1. GLOBAL: NAVBAR SCROLL EFFECT
   ========================================= */
document.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) navbar.classList.add('scrolled');
        else navbar.classList.remove('scrolled');
    }
});

function scrollToSection(event, targetId) {
    if (event) event.preventDefault(); 
    const element = document.getElementById(targetId);
    if (element) {
        const navbarHeight = 0; 
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - navbarHeight;
        window.scrollTo({ top: offsetPosition, behavior: "smooth" });
    }
}

/* =========================================
   2. HALAMAN: HOME & ABOUT
   ========================================= */
document.addEventListener('DOMContentLoaded', function () {
    const panduanButton = document.querySelector('a[href="#panduan"]');
    const targetSection = document.getElementById('panduan');
    if (panduanButton && targetSection) {
        panduanButton.addEventListener('click', function (e) {
            e.preventDefault();
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    const btnJelajahi = document.getElementById('btn-jelajahi');
    const btnLanjut = document.querySelector('.btn-lanjut');
    const cards = document.querySelectorAll('.knowledge-card');

    function scrollAbout(targetId) {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            const navbarHeight = 65;
            const elementPosition = targetElement.getBoundingClientRect().top + window.scrollY;
            window.scrollTo({ top: elementPosition - navbarHeight, behavior: "smooth" });
        }
    }

    if (btnJelajahi) btnJelajahi.addEventListener('click', (e) => { e.preventDefault(); scrollAbout('#definisi'); });
    if (btnLanjut) btnLanjut.addEventListener('click', (e) => { e.preventDefault(); scrollAbout('#pengetahuan'); });

    if (cards.length > 0) {
        cards.forEach(card => {
            card.addEventListener('click', function () {
                const isCurrentlyOpen = this.classList.contains('active');
                cards.forEach(c => {
                    c.classList.remove('active');
                    const label = c.querySelector('.toggle-text');
                    if (label) label.innerHTML = 'Klik untuk Lihat Detail &#9662;';
                });

                if (!isCurrentlyOpen) {
                    this.classList.add('active');
                    const label = this.querySelector('.toggle-text');
                    if (label) label.innerHTML = 'Tutup Detail &#9652;';
                    const details = this.querySelector('.knowledge-details');
                    if (details) {
                        setTimeout(() => {
                            details.scrollTo({ top: 0, behavior: 'smooth' });
                        }, 50);
                    }
                }
            });
        });
    }
});

/* =========================================
   3. HALAMAN: CLASSIFY - UPLOAD
   ========================================= */
document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.querySelector('.browse-btn');
    const previewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const classifyBtn = document.getElementById('classify-btn');
    const uploadArea = document.getElementById('upload-area');
    const backendError = document.getElementById('backend-error-data');

    if (backendError && backendError.value) {
        Swal.fire({
            icon: 'info',       // <-- Ganti 'error' jadi 'info' (ini yang bikin jadi ikon 'i' biru)
            title: 'Info',      // <-- Ganti 'Gagal' jadi 'Info' sesuai gambar
            text: backendError.value.replace(/\+/g, ' '), 
            confirmButtonColor: '#8a2be2', 
            confirmButtonText: 'OK',
            customClass: { popup: 'card-glass' }
        }).then(() => {
            // --- LOGIKA URL CLEANUP TETAP SAMA ---
            if (window.history.replaceState) {
                window.history.replaceState(null, null, window.location.pathname);
            }
        });
    }

    const resultLabel = document.getElementById("result-style");
    if (resultLabel) {
        if(previewContainer) previewContainer.hidden = true;
        if(uploadPlaceholder) uploadPlaceholder.hidden = false;
        if(fileInput) fileInput.value = '';
        if(classifyBtn) classifyBtn.disabled = true;
    }

    if (!fileInput) return;

    browseBtn.addEventListener('click', () => fileInput.click());

    function validateAndPreview(file) {
        if (!file) return false;
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            Swal.fire({ icon: 'error', title: 'Format Salah', text: 'Gunakan Format JPG/JPEG/PNG', confirmButtonColor: '#8a2be2', customClass: { popup: 'card-glass' } });
            resetUpload(); return false;
        }
        if (file.size > 5 * 1024 * 1024) {
            Swal.fire({ icon: 'warning', title: 'File Besar', text: 'Max 5MB', confirmButtonColor: '#8a2be2', customClass: { popup: 'card-glass' } });
            resetUpload(); return false;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            uploadPlaceholder.hidden = true;
            previewContainer.hidden = false;
            classifyBtn.disabled = false;
        }
        reader.readAsDataURL(file);
        return true;
    }

    function resetUpload() {
        fileInput.value = ''; imagePreview.src = '';
        uploadPlaceholder.hidden = false; previewContainer.hidden = true; classifyBtn.disabled = true;
    }

    fileInput.addEventListener('change', function () { validateAndPreview(this.files[0]); });
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => { uploadArea.classList.remove('dragover'); });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault(); uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (validateAndPreview(file)) fileInput.files = e.dataTransfer.files;
    });

    const removeBtn = document.getElementById('remove-image');
    if (removeBtn) removeBtn.addEventListener('click', resetUpload);
});

/* =========================================
   4. HALAMAN: CLASSIFY - CHATBOT
   ========================================= */
document.addEventListener("DOMContentLoaded", function() {
    const sendBtn = document.getElementById("send-btn");
    const chatInput = document.getElementById("chat-input");
    const chatWindow = document.getElementById("chat-window");
    const resultStyleElement = document.getElementById("result-style"); 
    const clearChatBtn = document.getElementById("clear-chat-btn");

    if (resultStyleElement) {
        if(chatInput) chatInput.disabled = false;
        if(sendBtn) sendBtn.disabled = false;
    }
    
    // 1. Load History (Akan return [] jika tamu)
    if (chatWindow) loadChatHistory();

    // 2. [LOGIKA BARU] Cek apakah ada Pesan Awal (Gambar) dari Upload?
    const initialMsgInput = document.getElementById('initial-chat-message');
    if (initialMsgInput && initialMsgInput.value) {
        let rawMsg = initialMsgInput.value;
        if (rawMsg.startsWith("[BOT]")) {
            rawMsg = rawMsg.replace("[BOT]", "");
        }
        
        // Tampilkan Pesan Gambar setelah jeda sedikit (agar history load duluan)
        setTimeout(() => {
            if (rawMsg.startsWith("[IMG_CARD]")) {
                renderImageCard(rawMsg);
            } else {
                appendMessage("bot", rawMsg);
            }
        }, 200); 
    }

    async function loadChatHistory() {
        try {
            const response = await fetch("/chat/history");
            const chats = await response.json();
            
            // Hapus isi chat HANYA jika TIDAK ada pesan awal (biar pesan gambar gak ilang)
            if (!initialMsgInput) {
                chatWindow.innerHTML = ""; 
            }

            // Jika Tamu (chats kosong) dan tidak ada upload baru (initialMsg kosong)
            if (chats.length === 0 && !initialMsgInput) {
                appendMessage("bot", "Halo! Silakan unggah gambar untuk memulai.");
            }
            
            chats.forEach(chat => {
                if (chat.message.startsWith("[BOT]")) {
                    const cleanMsg = chat.message.replace("[BOT]", "");
                    if (cleanMsg.startsWith("[IMG_CARD]")) renderImageCard(cleanMsg);
                    else appendMessage("bot", cleanMsg);
                } else {
                    appendMessage("user", chat.message);
                }
            });
            setTimeout(() => { chatWindow.scrollTop = chatWindow.scrollHeight; }, 100);
        } catch (error) { console.error("Gagal load history:", error); }
    }

    function renderImageCard(rawString) {
        const data = rawString.replace("[IMG_CARD]", "").split("|");
        const filename = data[0]; const label = data[1]; const confidence = data[2];
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", "bot");
        msgDiv.innerHTML = `
            <div class="msg-avatar"><span class="material-icons">auto_awesome</span></div>
            <div class="msg-bubble" style="background: #f0fdf4; border: 1px solid #bbf7d0; color: #1e293b; width: 100%; max-width: 320px;">
                <p style="margin-bottom: 8px; font-size: 0.85rem; font-weight: 600;">Hasil Analisis:</p>
                <img src="/storage/uploads/${filename}" style="width: 100%; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eee;">
                <h3 style="margin: 0; color: #16a34a; font-size: 1.1rem;">${label}</h3>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 5px;">
                    <span>Akurasi:</span><span style="font-weight: bold;">${confidence}</span>
                </div>
                <div class="confidence-bar-bg" style="height: 6px; background: #e2e8f0; border-radius: 3px; margin-top: 5px; overflow: hidden;">
                    <div class="confidence-fill" style="height: 100%; background: #16a34a; width: ${confidence}; transition: width 1s ease;"></div>
                </div>
            </div>`;
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    if (clearChatBtn) {
        clearChatBtn.addEventListener("click", async function(e) {
            e.preventDefault();
            
            const result = await Swal.fire({
                title: 'Hapus?', 
                text: "Riwayat chat dan hasil analisis akan dihapus.",
                icon: 'warning', 
                showCancelButton: true, 
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6', 
                confirmButtonText: 'Ya, Hapus!', 
                cancelButtonText: 'Batal', 
                customClass: { popup: 'card-glass' }
            });

            if (result.isConfirmed) {
                try {
                    // Panggil backend (Hapus data di DB jika login, atau dummy success jika tamu)
                    await fetch("/chat/history", { method: "DELETE" });
                    
                    // [PENTING] Redirect ke URL bersih untuk mengunci kembali
                    // Ini menghapus parameter ?img=... atau ?history_id=...
                    window.location.href = "/classify";
                    
                } catch (e) { 
                    console.error(e);
                    // Tetap paksa reload jika error
                    window.location.href = "/classify";
                }
            }
        });
    }

    if (sendBtn && chatInput) {
        async function sendMessage(textOverride = null) {
            const message = textOverride || chatInput.value.trim();
            if (!message) return;
            
            const resultStyleElement = document.getElementById("result-style");
            const currentArtStyle = resultStyleElement ? resultStyleElement.innerText.trim() : "Umum";
            
            const historyIdElement = document.getElementById("current-history-id");
            const historyId = historyIdElement && historyIdElement.value ? parseInt(historyIdElement.value) : null;
            
            let imageFilename = null;
            // Logic cari gambar di chat bubble (untuk dikirim ke AI sbg context)
            const allImages = chatWindow.querySelectorAll('.msg-bubble img');
            if (allImages.length > 0) {
                const lastImg = allImages[allImages.length - 1];
                const srcParts = lastImg.src.split('/'); 
                imageFilename = decodeURIComponent(srcParts[srcParts.length - 1]);
            }
            
            appendMessage("user", message);
            chatInput.value = "";
            const loadingId = "load-" + Date.now();
            appendMessage("bot", "Sedang mengetik...", false, loadingId);
            
            try {
                const response = await fetch("/chat", {
                    method: "POST", 
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        message: message, 
                        art_style: currentArtStyle, 
                        image_filename: imageFilename, 
                        history_id: historyId 
                    })
                });
                
                const data = await response.json();
                const loader = document.getElementById(loadingId);
                if (loader) loader.remove();
                
                if (response.ok) {
                    appendMessage("bot", data.reply);
                } else {
                    appendMessage("bot", "Maaf, terjadi kesalahan pada server.");
                }
            } catch (error) {
                const loader = document.getElementById(loadingId);
                if (loader) loader.remove();
                appendMessage("bot", "Maaf, koneksi terputus.");
            }
        }
        sendBtn.addEventListener("click", () => sendMessage());
        chatInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
        document.addEventListener("click", function(e) { if (e.target && e.target.classList.contains("chip")) { sendMessage(e.target.innerText); } });
    }

    function appendMessage(sender, text, isStatic = true, id = null) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", sender);
        if (id) msgDiv.id = id;
        const icon = sender === 'bot' ? 'smart_toy' : 'person';
        const formattedText = text.replace(/\n/g, '<br>');
        msgDiv.innerHTML = `<div class="msg-avatar"><span class="material-icons">${icon}</span></div><div class="msg-bubble">${formattedText}</div>`;
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

/* =========================================
   5. FUNGSI GLOBAL & MODAL HANDLERS
   (Admin Dashboard & Article Page)
   ========================================= */

// Toggle Dropdown Navbar
window.toggleUserMenu = function() {
    const dropdown = document.querySelector('.user-dropdown-container');
    if (dropdown) dropdown.classList.toggle('active');
};

// Toggle Password Visibility
window.togglePassword = function(inputId, iconElement) {
    const input = document.getElementById(inputId);
    if (input) {
        input.type = input.type === "password" ? "text" : "password";
        iconElement.innerText = input.type === "password" ? "visibility_off" : "visibility";
    }
};

// --- MODAL: CREATE USER (Admin) ---
window.openCreateModal = function() { 
    document.getElementById('createModal')?.classList.add('active'); 
    document.body.style.overflow = 'hidden';
};
window.closeCreateModal = function() { 
    document.getElementById('createModal')?.classList.remove('active'); 
    document.body.style.overflow = 'auto';
};

// --- MODAL: EDIT USER (Admin) ---
window.openEditModal = function(id, fullname, username, email, role) {
    const modal = document.getElementById('editModal');
    if (modal) {
        document.getElementById('edit_id').value = id;
        document.getElementById('edit_fullname').value = fullname;
        document.getElementById('edit_username').value = username;
        document.getElementById('edit_email').value = email;
        const roleSelect = document.getElementById('edit_role');
        if(roleSelect) roleSelect.value = role;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
};
window.closeEditModal = function() { 
    document.getElementById('editModal')?.classList.remove('active'); 
    document.body.style.overflow = 'auto';
};

// --- MODAL: ARTIKEL (Admin & Frontend) ---

// 1. [PENTING] Fungsi ini untuk FRONTEND (Article.html) - Membuka pop-up bacaan
window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; 
        setTimeout(() => {
            const scrollContent = modal.querySelector('.modal-scroll-content');
            if (scrollContent) scrollContent.scrollTop = 0; 
        }, 50);
    }
};

// 2. [PENTING] Fungsi ini untuk FRONTEND - Menutup pop-up bacaan
window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto'; 
    }
};

// 3. Fungsi Admin: Buka Modal Tambah Artikel (Kosong)
window.openArticleModal = function() {
    const modal = document.getElementById('articleModal');
    const form = document.getElementById('formArticle');
    const title = document.getElementById('articleModalTitle');
    if (modal && form) {
        form.reset();
        document.getElementById('art_id').value = ''; 
        title.innerText = "Tambah Konten";
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
};

// 4. Fungsi Admin: Buka Modal Edit Artikel (Isi Data)
window.openEditArticleModal = function(id, title, description, category, type, url) {
    const modal = document.getElementById('articleModal');
    const titleHeader = document.getElementById('articleModalTitle');
    
    if (modal) {
        document.getElementById('art_id').value = id;
        document.getElementById('art_title').value = title;
        document.getElementById('art_desc').value = description; // <--- INI YANG DITAMBAHKAN
        document.getElementById('art_category').value = category; 
        document.getElementById('art_type').value = type;
        document.getElementById('art_url').value = url;
        
        titleHeader.innerText = "Edit Artikel";
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
};

// 5. Fungsi Admin: Tutup Modal Artikel (Form)
window.closeArticleModal = function() {
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
};

// --- HAPUS USER ---
window.deleteUser = async function(userId, username) {
    const result = await Swal.fire({
        title: 'Hapus Pengguna?',
        text: `Akun @${username} akan dihapus permanen!`,
        icon: 'warning', showCancelButton: true, confirmButtonColor: '#ef4444',
        confirmButtonText: 'Ya, Hapus!', cancelButtonText: 'Batal', customClass: { popup: 'card-glass' }
    });

    if (result.isConfirmed) {
        try {
            const formData = new FormData();
            formData.append('user_id', userId); 
            const response = await fetch('/admin/delete-user', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.status === 'success') {
                Swal.fire({ icon: 'success', title: 'Terhapus', text: data.message, showConfirmButton: false, timer: 1500 });
                setTimeout(() => location.reload(), 1500);
            } else {
                Swal.fire('Gagal', data.message || 'Gagal menghapus pengguna.', 'error');
            }
        } catch (error) { Swal.fire('Error', 'Gagal menghubungi server.', 'error'); }
    }
};

// --- HAPUS ARTIKEL (REAL BACKEND) ---
window.deleteArticle = async function(id) {
    const result = await Swal.fire({
        title: 'Hapus Artikel?', 
        text: "Konten ini akan hilang permanen dari database.",
        icon: 'warning', 
        showCancelButton: true, 
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Ya, Hapus!',
        cancelButtonText: 'Batal',
        customClass: { popup: 'card-glass' }
    });

    if (result.isConfirmed) {
        try {
            const formData = new FormData();
            formData.append('article_id', id); // Kirim ID ke backend

            const response = await fetch('/admin/delete-article', { 
                method: 'POST', 
                body: formData 
            });
            const data = await response.json();

            if (data.status === 'success') {
                Swal.fire({ 
                    icon: 'success', 
                    title: 'Terhapus', 
                    text: data.message, 
                    showConfirmButton: false, 
                    timer: 1500 
                });
                setTimeout(() => location.reload(), 1500);
            } else {
                Swal.fire('Gagal', data.message, 'error');
            }
        } catch (error) {
            Swal.fire('Error', 'Gagal menghubungi server.', 'error');
        }
    }
};

// --- GLOBAL CLICK HANDLER (Tutup Modal saat klik luar) ---
window.onclick = function(event) {
    const c = document.getElementById('createModal');
    const e = document.getElementById('editModal');
    const a = document.getElementById('articleModal'); // Modal Artikel Admin
    const dropdown = document.querySelector('.user-dropdown-container');
    const btn = document.querySelector('.user-btn');

    // Tutup Modal Admin Spesifik
    if (event.target == c) window.closeCreateModal();
    if (event.target == e) window.closeEditModal();
    if (event.target == a) window.closeArticleModal();

    // Tutup Modal Umum (Frontend) pakai Class
    if (event.target.classList.contains('modal-overlay')) {
        event.target.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    // Tutup Dropdown
    if (dropdown && btn && !btn.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.remove('active');
    }
};

/* =========================================
   6. AJAX LISTENERS (ADMIN FORMS)
   ========================================= */
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Form Create User
    const formCreate = document.getElementById('formCreateUser');
    if (formCreate) {
        formCreate.addEventListener('submit', async function(e) {
            e.preventDefault(); e.stopImmediatePropagation();
            const btnSubmit = this.querySelector('button[type="submit"]');
            if (btnSubmit.disabled) return;
            const originalText = btnSubmit.innerText;
            btnSubmit.innerText = "Memproses..."; btnSubmit.disabled = true;
            const formData = new FormData(this);
            try {
                const response = await fetch('/admin/create-user', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    Swal.fire({ icon: 'success', title: 'Berhasil!', text: data.message, showConfirmButton: false, timer: 1500 });
                    setTimeout(() => location.reload(), 1500);
                } else if (data.status === 'exists') {
                    Swal.fire({ icon: 'warning', title: 'Akun Sudah Ada', text: data.message, confirmButtonColor: '#3085d6' })
                    .then(() => formCreate.reset());
                } else {
                    Swal.fire('Gagal', data.message, 'error');
                }
            } catch (error) {
                console.error(error); alert("Terjadi kesalahan sistem.");
            } finally {
                btnSubmit.innerText = originalText; btnSubmit.disabled = false;
            }
        });
    }

    // 2. Form Edit User
    const formEdit = document.getElementById('formEditUser');
    if (formEdit) {
        formEdit.addEventListener('submit', async function(e) {
            e.preventDefault();
            const btnSubmit = this.querySelector('button[type="submit"]');
            const originalText = btnSubmit.innerText;
            btnSubmit.innerText = "Menyimpan..."; btnSubmit.disabled = true;
            const formData = new FormData(this);
            try {
                const response = await fetch('/admin/edit-user', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    Swal.fire({ icon: 'success', title: 'Berhasil', text: data.message, showConfirmButton: false, timer: 1500 });
                    setTimeout(() => location.reload(), 1500);
                } else { Swal.fire('Gagal', data.message, 'error'); }
            } catch (error) { Swal.fire('Error', 'Terjadi kesalahan sistem', 'error'); } 
            finally { btnSubmit.innerText = originalText; btnSubmit.disabled = false; }
        });
    }

    // 3. Form Reset Password (Looping)
    const resetForms = document.querySelectorAll('.form-reset-pass');
    resetForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const btnSubmit = this.querySelector('button[type="submit"]');
            const originalText = btnSubmit.innerText;
            const result = await Swal.fire({
                title: 'Reset Password?', text: "Password akan diubah. User harus login dengan password baru.",
                icon: 'warning', showCancelButton: true, confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6', confirmButtonText: 'Ya, Reset!'
            });
            if (!result.isConfirmed) return;
            btnSubmit.innerText = "..."; btnSubmit.disabled = true;
            const formData = new FormData(this);
            try {
                const response = await fetch('/admin/reset-password', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    Swal.fire({ icon: 'success', title: 'Reset Berhasil', text: data.message, timer: 1500, showConfirmButton: false });
                    this.querySelector('input[type="password"]').value = '';
                } else { Swal.fire('Gagal', data.message, 'error'); }
            } catch (error) { Swal.fire('Error', 'Gagal menghubungi server', 'error'); } 
            finally { btnSubmit.innerText = originalText; btnSubmit.disabled = false; }
        });
    });

    // 4. Form Artikel (Admin Dashboard) - ANTI DOUBLE UPLOAD
    const formArticle = document.getElementById('formArticle');
    if (formArticle) {
        // Hapus listener lama (agar tidak menumpuk jika direload parsial)
        const newFormArticle = formArticle.cloneNode(true);
        formArticle.parentNode.replaceChild(newFormArticle, formArticle);

        newFormArticle.addEventListener('submit', async function(e) {
            e.preventDefault();
            e.stopImmediatePropagation(); // <--- Mencegah eksekusi ganda script
            
            // Cegah user klik tombol berkali-kali dengan cepat
            const btnSubmit = this.querySelector('button[type="submit"]');
            if (btnSubmit.disabled) return; 

            const originalText = btnSubmit.innerText;
            btnSubmit.innerText = "Menyimpan..."; 
            btnSubmit.disabled = true;

            const formData = new FormData(this);

            try {
                const response = await fetch('/admin/save-article', { 
                    method: 'POST', 
                    body: formData 
                });
                const data = await response.json();

                if (data.status === 'success') {
                    Swal.fire({
                        icon: 'success',
                        title: 'Berhasil!',
                        text: data.message,
                        showConfirmButton: false,
                        timer: 1500
                    });
                    window.closeArticleModal();
                    setTimeout(() => location.reload(), 1500);
                } else {
                    Swal.fire('Gagal', data.message, 'error');
                    btnSubmit.disabled = false; // Aktifkan lagi jika gagal
                    btnSubmit.innerText = originalText;
                }
            } catch (error) {
                console.error(error);
                Swal.fire('Error', 'Gagal menghubungi server.', 'error');
                btnSubmit.disabled = false;
                btnSubmit.innerText = originalText;
            }
        });
    }
});

