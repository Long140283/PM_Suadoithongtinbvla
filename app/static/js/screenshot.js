/**
 * Universal Screenshot and OCR Library
 * Supports capturing from other tabs, windows, and screens.
 */

const ScreenshotModule = (function() {
    let attachmentInput = null;
    let loadingModal = null;
    let captureHistory = [];
    let config = {};

    function init(cfg) {
        config = cfg;
        attachmentInput = document.querySelector(config.attachmentSelector || 'input[name="attachments"]');
        const modalEl = document.getElementById('loadingModal');
        if (modalEl && typeof bootstrap !== 'undefined') {
            loadingModal = new bootstrap.Modal(modalEl);
        }
        
        // Add history container if selector provided
        if (config.historySelector) {
            renderHistory();
        }
    }

    function attachFileToInput(blob, filename) {
        if (!attachmentInput) return;
        const file = new File([blob], filename, { type: blob.type });
        const dataTransfer = new DataTransfer();

        for (let i = 0; i < attachmentInput.files.length; i++) {
            dataTransfer.items.add(attachmentInput.files[i]);
        }

        dataTransfer.items.add(file);
        attachmentInput.files = dataTransfer.files;
        console.log('File attached:', filename);
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        attachmentInput.dispatchEvent(event);

        // Add to history
        const reader = new FileReader();
        reader.onload = (e) => {
            addToHistory({
                url: e.target.result,
                name: filename,
                timestamp: new Date()
            });
        };
        reader.readAsDataURL(blob);
    }

    function removeImage(index) {
        if (!confirm('Bạn có chắc chắn muốn xóa ảnh này không?')) return;
        
        // Remove from history
        captureHistory.splice(index, 1);
        
        // Remove from FileList (rebuild DataTransfer)
        const dataTransfer = new DataTransfer();
        const currentFiles = attachmentInput.files;
        for (let i = 0; i < currentFiles.length; i++) {
            if (i !== index) {
                dataTransfer.items.add(currentFiles[i]);
            }
        }
        attachmentInput.files = dataTransfer.files;
        
        // Refresh UI
        renderHistory();
        
        // Close preview modal
        const modalEl = document.getElementById('screenshotPreviewModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }

        // Trigger change event to notify other listeners
        const event = new Event('change', { bubbles: true });
        attachmentInput.dispatchEvent(event);
    }

    function addToHistory(item) {
        captureHistory.push(item);
        renderHistory();
    }

    function renderHistory() {
        if (!config.historySelector) return;
        const container = document.querySelector(config.historySelector);
        if (!container) return;

        if (captureHistory.length === 0) {
            container.innerHTML = '<p class="text-muted small">Chưa có ảnh chụp nào.</p>';
            return;
        }

        container.innerHTML = `
            <div class="d-flex flex-wrap gap-2 mt-2">
                ${captureHistory.map((item, index) => `
                    <div class="position-relative screenshot-thumb" style="width: 80px; height: 80px; cursor: pointer;">
                        <img src="${item.url}" class="img-thumbnail w-100 h-100 object-fit-cover" 
                             onclick="ScreenshotModule.previewImage(${index})" title="${item.name}">
                        <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 p-0" 
                                style="width: 20px; height: 20px; font-size: 10px;" 
                                onclick="event.stopPropagation(); ScreenshotModule.removeImage(${index})">
                            &times;
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function previewImage(index) {
        const item = captureHistory[index];
        if (!item) return;

        // Simple preview modal or open in new tab
        const modalId = 'screenshotPreviewModal';
        let modalEl = document.getElementById(modalId);
        
        if (!modalEl) {
            modalEl = document.createElement('div');
            modalEl.id = modalId;
            modalEl.className = 'modal fade';
            modalEl.tabIndex = -1;
            modalEl.innerHTML = `
                <div class="modal-dialog modal-xl modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Xem lại ảnh chụp</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center bg-dark">
                            <img src="" id="preview-img" class="img-fluid">
                        </div>
                        <div class="modal-footer">
                            <button type="button" id="preview-ocr-btn" class="btn btn-success"><i class="fas fa-file-invoice me-2"></i>Trích xuất thông tin</button>
                            <button type="button" id="preview-delete-btn" class="btn btn-danger"><i class="fas fa-trash-alt me-2"></i>Xóa ảnh</button>
                            <a href="" id="preview-download" download class="btn btn-primary"><i class="fas fa-download me-2"></i>Tải về</a>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Đóng</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modalEl);
        }

        const img = modalEl.querySelector('#preview-img');
        const download = modalEl.querySelector('#preview-download');
        const ocrBtn = modalEl.querySelector('#preview-ocr-btn');
        const deleteBtn = modalEl.querySelector('#preview-delete-btn');
        
        img.src = item.url;
        download.href = item.url;
        download.download = item.name;

        const modal = new bootstrap.Modal(modalEl);
        
        ocrBtn.onclick = () => {
            modal.hide();
            performOCR(item.url);
        };

        deleteBtn.onclick = () => {
            removeImage(index);
        };

        modal.show();
    }

    async function listWindows() {
        if (loadingModal) {
            const body = document.querySelector('#loadingModal .modal-body p');
            if (body) body.innerText = "Đang lấy danh sách các tác vụ đang mở...";
            loadingModal.show();
        }

        try {
            const response = await fetch('/api/screenshot/list_windows');
            const data = await response.json();
            if (data.status === 'success') {
                showWindowSelectionModal(data.windows);
            } else {
                alert('Không thể lấy danh sách cửa sổ: ' + data.message);
            }
        } catch (err) {
            console.error('Error listing windows:', err);
            alert('Lỗi hệ thống khi lấy danh sách cửa sổ.');
        } finally {
            if (loadingModal) {
                loadingModal.hide();
                const body = document.querySelector('#loadingModal .modal-body p');
                if (body) body.innerText = "Vui lòng đợi trong khi hệ thống đang đọc thông tin từ hình ảnh.";
            }
        }
    }


    function showWindowSelectionModal(windows) {
        const modalId = 'windowSelectionModal';
        let modalEl = document.getElementById(modalId);
        
        if (!modalEl) {
            modalEl = document.createElement('div');
            modalEl.id = modalId;
            modalEl.className = 'modal fade';
            modalEl.tabIndex = -1;
            modalEl.innerHTML = `
                <div class="modal-dialog modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Chọn tác vụ để chụp</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="list-group" id="window-list"></div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modalEl);
        }

        const list = modalEl.querySelector('#window-list');
        list.innerHTML = windows.map(w => `
            <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" 
                    onclick="ScreenshotModule.takeNativeRegionScreenshot(${w.hwnd}, 'task')">
                <span class="text-truncate" style="max-width: 80%">${w.title}</span>
                <span class="badge bg-secondary rounded-pill">PID: ${w.pid}</span>
            </button>
        `).join('');

        const modal = new bootstrap.Modal(modalEl);
        modal.show();
        
        // Auto-close modal when a selection is made
        list.addEventListener('click', () => modal.hide());
    }

    async function takeNativeRegionScreenshot(hwnd = null, mode = 'region') {
        if (loadingModal) {
            const body = document.querySelector('#loadingModal .modal-body p');
            if (body) {
                if (mode === 'task') {
                    body.innerText = "Đang chụp ảnh tác vụ...";
                } else {
                    body.innerText = "Hệ thống đang mở công cụ chọn vùng. Vui lòng rê chuột và quét vùng cần chụp trên màn hình. Nhấn ESC để hủy.";
                }
            }
            loadingModal.show();
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const response = await fetch('/api/screenshot/native_capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ hwnd: hwnd, mode: mode, perform_ocr: false })
            });

            const result = await response.json();
            if (result.status === 'success') {
                const imgResponse = await fetch(result.url);
                const blob = await imgResponse.blob();
                attachFileToInput(blob, `native-capture-${Date.now()}.png`);
                
                // OCR is now manual via preview to save time
                /*
                if (result.ocr_data) {
                    processOCRData(result.ocr_data);
                }
                */
            } else if (result.status === 'cancelled') {
                console.log('Capture cancelled by user');
            } else {
                throw new Error(result.message);
            }
        } catch (err) {
            console.warn("Native capture failed, falling back to browser:", err);
            if (!hwnd) takeBrowserRegionScreenshot();
        } finally {
            if (loadingModal) {
                loadingModal.hide();
                // Reset loading text
                const body = document.querySelector('#loadingModal .modal-body p');
                if (body) body.innerText = "Vui lòng đợi trong khi hệ thống đang đọc thông tin từ hình ảnh.";
            }
        }
    }

    async function takeBrowserRegionScreenshot() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
            alert("Tính năng 'Chụp theo vùng' không khả dụng trên trình duyệt này (Yêu cầu HTTPS hoặc localhost).");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: { cursor: "always", displaySurface: "monitor" },
                audio: false
            });

            const video = document.createElement('video');
            video.srcObject = stream;
            
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });

            await new Promise(r => setTimeout(r, 500));

            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            stream.getTracks().forEach(track => track.stop());
            showRegionSelectionOverlay(canvas);

        } catch (err) {
            console.error("Error in takeBrowserRegionScreenshot:", err);
        }
    }

    async function takeUniversalRegionScreenshot() {
        await takeNativeRegionScreenshot();
    }

    async function takeNativeCameraCapture() {
        if (loadingModal) {
            const body = document.querySelector('#loadingModal .modal-body p');
            if (body) body.innerText = "Đang mở Camera trên máy tính... Vui lòng nhấn ENTER để chụp hoặc ESC để hủy.";
            loadingModal.show();
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const response = await fetch('/api/screenshot/native_camera', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            const result = await response.json();
            if (result.status === 'success') {
                const imgResponse = await fetch(result.url);
                const blob = await imgResponse.blob();
                attachFileToInput(blob, `camera-native-${Date.now()}.png`);
            } else if (result.status === 'cancelled') {
                console.log('Camera capture cancelled by user');
            } else {
                throw new Error(result.message);
            }
        } catch (err) {
            console.error("Native camera capture failed:", err);
            let msg = "Lỗi khi mở camera trên máy tính: " + err.message;
            if (err.message.includes("Could not open camera")) {
                msg += "\n\nGợi ý: \n1. Kiểm tra camera có đang bị ứng dụng khác (Zoom, Teams, Zalo...) sử dụng không.\n2. Kiểm tra 'Cài đặt quyền riêng tư' (Privacy Settings) trên Windows có cho phép ứng dụng truy cập Camera không.";
            }
            alert(msg);
        } finally {
            if (loadingModal) loadingModal.hide();
        }
    }

    function showRegionSelectionOverlay(sourceCanvas) {
        const overlay = document.createElement('div');
        overlay.id = 'universal-capture-overlay';
        Object.assign(overlay.style, {
            position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.8)', zIndex: '999999', cursor: 'crosshair',
            display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden'
        });

        const img = document.createElement('img');
        img.src = sourceCanvas.toDataURL('image/png');
        Object.assign(img.style, { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', userSelect: 'none', pointerEvents: 'none' });

        const container = document.createElement('div');
        Object.assign(container.style, { position: 'relative', display: 'inline-block' });
        container.appendChild(img);
        overlay.appendChild(container);
        document.body.appendChild(overlay);

        const selectionBox = document.createElement('div');
        Object.assign(selectionBox.style, {
            position: 'absolute', border: '2px solid #007bff', backgroundColor: 'rgba(0, 123, 255, 0.1)',
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.5)', display: 'none', pointerEvents: 'none'
        });
        container.appendChild(selectionBox);

        const toolbar = document.createElement('div');
        Object.assign(toolbar.style, {
            position: 'absolute', display: 'none', backgroundColor: 'rgba(255, 255, 255, 0.95)',
            padding: '8px', borderRadius: '8px', boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
            zIndex: '1000000', gap: '8px', backdropFilter: 'blur(5px)'
        });
        
        const btnStyle = "padding: 6px 16px; cursor: pointer; border: none; border-radius: 6px; font-weight: 600; font-size: 14px; transition: all 0.2s;";
        
        const scanBtn = document.createElement('button');
        scanBtn.innerHTML = '<i class="fas fa-search"></i> Xác nhận & Quét';
        scanBtn.style.cssText = btnStyle + "background-color: #007bff; color: white;";

        const cancelBtn = document.createElement('button');
        cancelBtn.innerHTML = 'Hủy';
        cancelBtn.style.cssText = btnStyle + "background-color: #6c757d; color: white;";

        toolbar.appendChild(scanBtn);
        toolbar.appendChild(cancelBtn);
        overlay.appendChild(toolbar);

        let isDragging = false;
        let startX, startY;
        let rect = { x: 0, y: 0, w: 0, h: 0 };

        container.onmousedown = (e) => {
            isDragging = true;
            const bounds = container.getBoundingClientRect();
            startX = e.clientX - bounds.left;
            startY = e.clientY - bounds.top;
            selectionBox.style.display = 'block';
            selectionBox.style.left = startX + 'px';
            selectionBox.style.top = startY + 'px';
            selectionBox.style.width = '0px';
            selectionBox.style.height = '0px';
            toolbar.style.display = 'none';
        };

        window.onmousemove = (e) => {
            if (!isDragging) return;
            const bounds = container.getBoundingClientRect();
            let currentX = e.clientX - bounds.left;
            let currentY = e.clientY - bounds.top;
            currentX = Math.max(0, Math.min(currentX, bounds.width));
            currentY = Math.max(0, Math.min(currentY, bounds.height));
            const width = currentX - startX;
            const height = currentY - startY;
            rect.x = width > 0 ? startX : currentX;
            rect.y = height > 0 ? startY : currentY;
            rect.w = Math.abs(width);
            rect.h = Math.abs(height);
            selectionBox.style.left = rect.x + 'px';
            selectionBox.style.top = rect.y + 'px';
            selectionBox.style.width = rect.w + 'px';
            selectionBox.style.height = rect.h + 'px';
        };

        window.onmouseup = () => {
            if (!isDragging) return;
            isDragging = false;
            if (rect.w > 10 && rect.h > 10) {
                const bounds = container.getBoundingClientRect();
                toolbar.style.display = 'flex';
                let tTop = rect.y + rect.h + 10;
                if (tTop + 50 > bounds.height) tTop = rect.y - 50;
                toolbar.style.top = (tTop + bounds.top) + 'px';
                toolbar.style.left = (rect.x + bounds.left + rect.w/2 - 100) + 'px';
            }
        };

        scanBtn.onclick = async () => {
            const bounds = container.getBoundingClientRect();
            const scaleX = sourceCanvas.width / bounds.width;
            const scaleY = sourceCanvas.height / bounds.height;
            const finalCanvas = document.createElement('canvas');
            finalCanvas.width = rect.w * scaleX;
            finalCanvas.height = rect.h * scaleY;
            const fCtx = finalCanvas.getContext('2d');
            fCtx.drawImage(sourceCanvas, rect.x * scaleX, rect.y * scaleY, rect.w * scaleX, rect.h * scaleY, 0, 0, finalCanvas.width, finalCanvas.height);
            document.body.removeChild(overlay);
            finalCanvas.toBlob(blob => {
                attachFileToInput(blob, `capture-region-${Date.now()}.png`);
                performOCR(blob);
            }, 'image/png');
        };

        cancelBtn.onclick = () => document.body.removeChild(overlay);
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                if (document.body.contains(overlay)) document.body.removeChild(overlay);
                window.removeEventListener('keydown', escHandler);
            }
        };
        window.addEventListener('keydown', escHandler);
    }



    async function performOCR(imageSource) {
        if (!window.Tesseract) {
            console.warn("Tesseract.js not loaded.");
            return;
        }

        if (loadingModal) {
            const body = document.querySelector('#loadingModal .modal-body p');
            if (body) body.innerText = "Đang nhận diện chữ từ hình ảnh...";
            loadingModal.show();
        }

        try {
            const result = await Tesseract.recognize(imageSource, 'vie+eng');
            const text = result.data.text;
            console.log("OCR Result:", text);
            
            // Send to server to extract structured data
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const response = await fetch('/api/screenshot/extract_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ text: text })
            });
            
            const data = await response.json();
            if (data.status === 'success' && data.ocr_data) {
                processOCRData(data.ocr_data);
            }
        } catch (err) {
            console.error("OCR Error:", err);
        } finally {
            if (loadingModal) loadingModal.hide();
        }
    }

    function processOCRData(data) {
        Object.keys(data).forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.value = data[id];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    return {
        init: init,
        takeUniversalRegionScreenshot: takeUniversalRegionScreenshot,
        takeNativeRegionScreenshot: takeNativeRegionScreenshot,
        takeNativeCameraCapture: takeNativeCameraCapture,
        listWindows: listWindows,
        previewImage: previewImage,
        performOCR: performOCR,
        attachFileToInput: attachFileToInput,
        removeImage: removeImage
    };
})();

