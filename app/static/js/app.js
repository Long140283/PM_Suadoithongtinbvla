// Custom JavaScript for patient management app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Patient management app loaded');

    // Image Viewer Logic
    const imageLinks = document.querySelectorAll('.image-viewer-link');
    const modal = document.getElementById('imageViewerModal');
    const ivImage = document.getElementById('iv-image');
    const rotateBtn = document.getElementById('iv-rotate');
    const zoomInBtn = document.getElementById('iv-zoom-in');
    const zoomOutBtn = document.getElementById('iv-zoom-out');
    const downloadBtn = document.getElementById('iv-download');
    const zoomInfo = document.querySelector('.iv-zoom-info');

    let currentRotation = 0;
    let currentScale = 1;

    if (modal) {
        const bsModal = new bootstrap.Modal(modal);

        imageLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const imageUrl = this.getAttribute('href');
                const filename = this.getAttribute('data-filename') || 'image.jpg';
                
                // Đảm bảo lấy link ảnh thô (raw) thay vì trang HTML viewer
                const rawImageUrl = imageUrl + (imageUrl.includes('?') ? '&' : '?') + 'raw=1';
                ivImage.src = rawImageUrl;
                document.querySelector('#imageViewerModal .modal-title').textContent = filename;
                
                // Reset state
                currentRotation = 0;
                currentScale = 1;
                updateImageTransform();
                
                bsModal.show();
            });
        });

        rotateBtn.addEventListener('click', () => {
            currentRotation = (currentRotation + 90) % 360;
            updateImageTransform();
        });

        zoomInBtn.addEventListener('click', () => {
            currentScale += 0.2;
            updateImageTransform();
        });

        zoomOutBtn.addEventListener('click', () => {
            if (currentScale > 0.4) {
                currentScale -= 0.2;
                updateImageTransform();
            }
        });

        downloadBtn.addEventListener('click', () => {
            const link = document.createElement('a');
            link.href = ivImage.src;
            link.download = document.querySelector('#imageViewerModal .modal-title').textContent;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });

        function updateImageTransform() {
            ivImage.style.transform = `rotate(${currentRotation}deg) scale(${currentScale})`;
            if (zoomInfo) {
                zoomInfo.textContent = `${Math.round(currentScale * 100)}%`;
            }
        }
        
        // Handle image drag
        let isDragging = false;
        let startX, startY, scrollLeft, scrollTop;

        const container = document.querySelector('.iv-container');
        
        ivImage.addEventListener('mousedown', (e) => {
            isDragging = true;
            ivImage.style.cursor = 'grabbing';
            startX = e.pageX - container.offsetLeft;
            startY = e.pageY - container.offsetTop;
            scrollLeft = container.scrollLeft;
            scrollTop = container.scrollTop;
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
            ivImage.style.cursor = 'grab';
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const y = e.pageY - container.offsetTop;
            const walkX = (x - startX) * 2;
            const walkY = (y - startY) * 2;
            container.scrollLeft = scrollLeft - walkX;
            container.scrollTop = scrollTop - walkY;
        });
    }
});
