/**
 * Sakura Overlay Effect by Kazaki Rio
 * วิธีใช้: new SakuraOverlay('target-element-id', { ...options });
 */
class SakuraOverlay {
    constructor(elementId, options = {}) {
        this.container = document.getElementById(elementId);
        if (!this.container) {
            console.error(`SakuraOverlay: ไม่พบ Element ID '${elementId}'`);
            return;
        }

        // การตั้งค่า Default (แบบที่ปรับจูนมาแล้วว่าสวย)
        this.config = Object.assign({
            totalPetals: 15,       // จำนวนกลีบ
            minSize: 5,            // ขนาดเล็กสุด
            maxSize: 8,            // ขนาดใหญ่สุด
            baseSpeed: 0.1,        // ความเร็วพื้นฐาน
            colors: [
                ['rgba(255, 183, 178, 1)', 'rgba(215, 143, 138, 1)'], 
                ['rgba(255, 209, 220, 1)', 'rgba(215, 169, 180, 1)'], 
                ['rgba(255, 228, 225, 1)', 'rgba(215, 188, 185, 1)'], 
                ['rgba(255, 240, 245, 1)', 'rgba(215, 200, 205, 1)'], 
            ],
            thickness: 3 
        }, options);

        this.petals = [];
        this.width = 0;
        this.height = 0;
        this.animationFrameId = null;

        // SVG Path ของดอกซากุระ
        const petalSVG = "M0,0 C0,0 15,-10 15,-30 C15,-55 5,-60 0,-50 C-5,-60 -15,-55 -15,-30 C-15,-10 0,0 0,0";
        this.petalPath = new Path2D(petalSVG);

        this.initCanvas();
        this.resize();
        this.initPetals();
        this.animate();

        // ตรวจจับการเปลี่ยนขนาดของ Element หลัก
        this.resizeObserver = new ResizeObserver(() => this.resize());
        this.resizeObserver.observe(this.container);
    }

    initCanvas() {
        // ตรวจสอบ position ของ container ถ้าเป็น static ให้เปลี่ยนเป็น relative 
        // เพื่อให้ canvas absolute เกาะอยู่ภายในได้
        const style = window.getComputedStyle(this.container);
        if (style.position === 'static') {
            this.container.style.position = 'relative';
        }

        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none'; // ให้คลิกทะลุได้
        this.canvas.style.zIndex = '10'; // อยู่บนสุดใน container นั้น
        
        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);
    }

    resize() {
        this.width = this.container.offsetWidth;
        this.height = this.container.offsetHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }

    initPetals() {
        this.petals = [];
        for (let i = 0; i < this.config.totalPetals; i++) {
            this.petals.push(new SakuraPetal(this.width, this.height, this.config, this.petalPath));
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        this.petals.forEach(petal => {
            petal.update(this.width, this.height);
            petal.draw(this.ctx);
        });

        this.animationFrameId = requestAnimationFrame(() => this.animate());
    }

    // ฟังก์ชันสำหรับหยุดและลบเอฟเฟกต์
    destroy() {
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
        if (this.resizeObserver) this.resizeObserver.disconnect();
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// คลาสลูกสำหรับจัดการแต่ละกลีบ (แยกออกมาเพื่อความสะอาด)
class SakuraPetal {
    constructor(width, height, config, path) {
        this.config = config;
        this.path = path;
        this.init(width, height, true);
    }

    init(width, height, startRandomY = false) {
        this.x = Math.random() * width;
        this.y = startRandomY ? Math.random() * height : -50;
        this.size = this.config.minSize + Math.random() * (this.config.maxSize - this.config.minSize);
        
        this.speedY = (this.size / this.config.maxSize) * this.config.baseSpeed + 0.05 + Math.random() * 0.05;
        this.speedX = -0.3 - Math.random() * 0.2; // ลมพัดซ้าย

        this.rotation = Math.random() * 360;
        this.rotationSpeed = (Math.random() - 0.5) * 0.01;

        this.flip = Math.random() * Math.PI;
        this.flipSpeed = Math.random() * 0.02 + 0.005;

        this.sway = Math.random() * 0.005; 
        this.swayPhase = Math.random() * Math.PI * 2;

        const colorPair = this.config.colors[Math.floor(Math.random() * this.config.colors.length)];
        this.mainColor = colorPair[0];
        this.depthColor = colorPair[1];
        
        this.type = Math.random() > 0.8 ? 'flower' : 'petal';
    }

    update(width, height) {
        this.y += this.speedY;
        this.swayPhase += this.sway;
        this.x += this.speedX + Math.sin(this.swayPhase) * 0.1;

        this.rotation += this.rotationSpeed;
        this.flip += this.flipSpeed;

        // Reset เมื่อตกเลยขอบ
        if (this.y > height + 50 || this.x < -50) {
            if (Math.random() > 0.5) {
                this.x = width + 20; 
                this.y = Math.random() * height; 
            } else {
                this.x = Math.random() * width;
                this.y = -50;
            }
            // รีเซ็ตความเร็วใหม่ตามขนาด
            this.speedY = (this.size / this.config.maxSize) * this.config.baseSpeed + 0.05 + Math.random() * 0.05;
        }
    }

    draw(ctx) {
        const scaleY = Math.cos(this.flip);
        const thicknessOffset = Math.sin(this.flip) * this.config.thickness;
        const scaleFactor = this.size / 40; // SVG Reference size

        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);

        const layers = 4; // จำนวนชั้นความหนา
        
        // วาดชั้น Depth
        for (let i = layers; i > 0; i--) {
            ctx.save();
            const currentOffset = -(thicknessOffset * (i / layers));
            ctx.translate(0, currentOffset);
            ctx.scale(scaleFactor, scaleFactor * scaleY);
            ctx.fillStyle = this.depthColor;
            
            if (this.type === 'petal') ctx.fill(this.path);
            else this.drawFlowerShape(ctx, this.path);
            
            ctx.restore();
        }

        // วาดชั้นบนสุด
        ctx.save();
        ctx.scale(scaleFactor, scaleFactor * scaleY);
        ctx.fillStyle = this.mainColor;
        
        if (this.type === 'petal') ctx.fill(this.path);
        else this.drawFlowerShape(ctx, this.path);
        
        ctx.restore();
        ctx.restore();
    }

    drawFlowerShape(ctx, path) {
        for (let i = 0; i < 5; i++) {
            ctx.save();
            ctx.rotate((Math.PI * 2 * i) / 5);
            ctx.fill(path);
            ctx.restore();
        }
        ctx.beginPath();
        ctx.arc(0, 0, 5, 0, Math.PI*2);
        ctx.fillStyle = "rgba(255, 255, 230, 0.5)";
        ctx.fill();
    }
}