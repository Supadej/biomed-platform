/**
 * RangeSlider Component for daisyUI
 * A customizable range slider with single or dual handles
 * 
 * Usage:
 * const slider = new RangeSlider('containerId', {
 *     min: 0,
 *     max: 100,
 *     value: 50,           // Single value or [min, max] for range
 *     step: 1,
 *     range: false,        // true for dual handles
 *     showTooltip: true,
 *     showLabels: true,
 *     formatValue: (val) => val.toLocaleString(),
 *     onChange: (value) => console.log(value)
 * });
 */

class RangeSlider {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`RangeSlider: Container #${containerId} not found`);
            return;
        }

        // Default text labels
        const defaultText = {
            min: 'Min',
            max: 'Max',
            from: 'From',
            to: 'To'
        };

        // Configuration with defaults
        this.config = {
            min: config.min ?? 0,
            max: config.max ?? 100,
            step: config.step ?? 1,
            value: config.value ?? (config.range ? [config.min ?? 0, config.max ?? 100] : config.min ?? 0),
            range: config.range ?? false,
            showTooltip: config.showTooltip !== false,
            showLabels: config.showLabels !== false,
            showInputs: config.showInputs ?? false,
            showScale: config.showScale ?? false,
            showFill: config.showFill !== false, // Show filled track (default: true)
            scaleSteps: config.scaleSteps ?? 5,
            colorClass: config.colorClass ?? 'range-primary',
            size: config.size ?? '', // '', 'range-xs', 'range-sm', 'range-lg'
            disabled: config.disabled ?? false,
            text: { ...defaultText, ...(config.text || {}) },
            formatValue: config.formatValue || ((val) => val.toLocaleString()),
            onChange: config.onChange || (() => {}),
            onSlideStart: config.onSlideStart || (() => {}),
            onSlideEnd: config.onSlideEnd || (() => {})
        };

        // Current values
        if (this.config.range) {
            this.values = Array.isArray(this.config.value) 
                ? [...this.config.value] 
                : [this.config.min, this.config.value];
        } else {
            this.values = [Array.isArray(this.config.value) ? this.config.value[0] : this.config.value];
        }

        this.isDragging = false;
        this.activeHandle = null;

        this.render();
        this.bindEvents();
        this.updateUI();
    }

    render() {
        const { min, max, range, showLabels, showInputs, showScale, showFill, colorClass, size, disabled } = this.config;
        
        // Map color class to CSS variable colors (works with daisyUI v5)
        const colorMap = {
            'range-primary': { cssVar: 'var(--color-primary)', border: 'border-primary' },
            'range-secondary': { cssVar: 'var(--color-secondary)', border: 'border-secondary' },
            'range-accent': { cssVar: 'var(--color-accent)', border: 'border-accent' },
            'range-success': { cssVar: 'var(--color-success)', border: 'border-success' },
            'range-warning': { cssVar: 'var(--color-warning)', border: 'border-warning' },
            'range-error': { cssVar: 'var(--color-error)', border: 'border-error' },
            'range-info': { cssVar: 'var(--color-info)', border: 'border-info' }
        };
        const colors = colorMap[colorClass] || colorMap['range-primary'];

        this.container.innerHTML = `
            <div class="range-slider ${disabled ? 'opacity-50 pointer-events-none' : ''}" data-rs-root>
                ${showLabels ? `
                    <div class="flex justify-between items-center mb-2 text-sm">
                        <span class="text-base-content/60" data-rs-label-min>${range ? this.config.text.from : this.config.text.min}: <span class="font-semibold text-base-content" data-rs-value-min></span></span>
                        ${range ? `<span class="text-base-content/60" data-rs-label-max>${this.config.text.to}: <span class="font-semibold text-base-content" data-rs-value-max></span></span>` : ''}
                    </div>
                ` : ''}
                
                <div class="relative py-2" data-rs-track-container>
                    <!-- Track background -->
                    <div class="relative h-2 bg-base-300 rounded-full" data-rs-track>
                        <!-- Filled track (optional) - use inline style for color -->
                        ${showFill ? `<div class="absolute top-0 h-full rounded-full transition-all" style="background-color: ${colors.cssVar};" data-rs-fill></div>` : ''}
                        
                        <!-- Handles -->
                        <div class="absolute w-5 h-5 bg-base-100 border-2 ${colors.border} rounded-full cursor-pointer shadow-md hover:scale-110 transition-transform flex items-center justify-center" data-rs-handle="0" style="top: 50%; transform: translateY(-50%);">
                            ${this.config.showTooltip ? `
                                <div class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-neutral text-neutral-content text-xs rounded shadow-lg opacity-0 transition-opacity pointer-events-none whitespace-nowrap" data-rs-tooltip="0"></div>
                            ` : ''}
                        </div>
                        
                        ${range ? `
                            <div class="absolute w-5 h-5 bg-base-100 border-2 ${colors.border} rounded-full cursor-pointer shadow-md hover:scale-110 transition-transform flex items-center justify-center" data-rs-handle="1" style="top: 50%; transform: translateY(-50%);">
                                ${this.config.showTooltip ? `
                                    <div class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-neutral text-neutral-content text-xs rounded shadow-lg opacity-0 transition-opacity pointer-events-none whitespace-nowrap" data-rs-tooltip="1"></div>
                                ` : ''}
                            </div>
                        ` : ''}
                    </div>
                    
                    ${showScale ? `
                        <div class="flex justify-between mt-1 text-xs text-base-content/50" data-rs-scale>
                            ${this.renderScale()}
                        </div>
                    ` : ''}
                </div>
                
                ${showInputs ? `
                    <div class="flex gap-2 mt-3">
                        <div class="flex-1">
                            <input type="number" 
                                class="input input-sm input-bordered w-full" 
                                min="${min}" max="${max}" step="${this.config.step}"
                                data-rs-input="0"
                                placeholder="${range ? this.config.text.from : this.config.text.min}">
                        </div>
                        ${range ? `
                            <span class="flex items-center text-base-content/50">—</span>
                            <div class="flex-1">
                                <input type="number" 
                                    class="input input-sm input-bordered w-full" 
                                    min="${min}" max="${max}" step="${this.config.step}"
                                    data-rs-input="1"
                                    placeholder="${this.config.text.to}">
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;

        // Store references
        this.root = this.container.querySelector('[data-rs-root]');
        this.track = this.container.querySelector('[data-rs-track]');
        this.fill = this.container.querySelector('[data-rs-fill]');
        console.log('RangeSlider fill element:', this.fill, 'showFill:', this.config.showFill);
        this.handles = this.container.querySelectorAll('[data-rs-handle]');
        this.tooltips = this.container.querySelectorAll('[data-rs-tooltip]');
        this.inputs = this.container.querySelectorAll('[data-rs-input]');
        this.valueDisplays = {
            min: this.container.querySelector('[data-rs-value-min]'),
            max: this.container.querySelector('[data-rs-value-max]')
        };
    }

    renderScale() {
        const { min, max, scaleSteps } = this.config;
        const step = (max - min) / scaleSteps;
        let html = '';
        for (let i = 0; i <= scaleSteps; i++) {
            const value = min + (step * i);
            html += `<span>${this.config.formatValue(Math.round(value))}</span>`;
        }
        return html;
    }

    bindEvents() {
        // Handle drag
        this.handles.forEach((handle, index) => {
            handle.addEventListener('mousedown', (e) => this.startDrag(e, index));
            handle.addEventListener('touchstart', (e) => this.startDrag(e, index), { passive: false });
        });

        // Track click
        this.track.addEventListener('click', (e) => this.handleTrackClick(e));

        // Global mouse/touch events
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.endDrag());
        document.addEventListener('touchmove', (e) => this.drag(e), { passive: false });
        document.addEventListener('touchend', () => this.endDrag());

        // Input events
        this.inputs.forEach((input, index) => {
            input.addEventListener('change', (e) => {
                let value = parseFloat(e.target.value) || this.config.min;
                value = Math.max(this.config.min, Math.min(this.config.max, value));
                this.setValue(index, value);
            });
        });

        // Show/hide tooltips on hover
        this.handles.forEach((handle, index) => {
            handle.addEventListener('mouseenter', () => this.showTooltip(index));
            handle.addEventListener('mouseleave', () => {
                if (!this.isDragging) this.hideTooltip(index);
            });
        });
    }

    startDrag(e, index) {
        if (this.config.disabled) return;
        e.preventDefault();
        this.isDragging = true;
        this.activeHandle = index;
        this.showTooltip(index);
        this.handles[index].classList.add('scale-125', 'z-10');
        this.config.onSlideStart(this.getValues());
    }

    drag(e) {
        if (!this.isDragging || this.activeHandle === null) return;
        e.preventDefault();

        const rect = this.track.getBoundingClientRect();
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        const value = this.config.min + (percent * (this.config.max - this.config.min));
        const steppedValue = this.snapToStep(value);

        this.setValue(this.activeHandle, steppedValue);
    }

    endDrag() {
        if (!this.isDragging) return;
        
        if (this.activeHandle !== null) {
            this.handles[this.activeHandle].classList.remove('scale-125', 'z-10');
            this.hideTooltip(this.activeHandle);
        }
        
        this.isDragging = false;
        this.activeHandle = null;
        this.config.onSlideEnd(this.getValues());
    }

    handleTrackClick(e) {
        if (this.config.disabled) return;
        
        const rect = this.track.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const value = this.config.min + (percent * (this.config.max - this.config.min));
        const steppedValue = this.snapToStep(value);

        if (this.config.range) {
            // Find closest handle
            const dist0 = Math.abs(this.values[0] - steppedValue);
            const dist1 = Math.abs(this.values[1] - steppedValue);
            const index = dist0 <= dist1 ? 0 : 1;
            this.setValue(index, steppedValue);
        } else {
            this.setValue(0, steppedValue);
        }
    }

    snapToStep(value) {
        const { min, step } = this.config;
        return Math.round((value - min) / step) * step + min;
    }

    setValue(index, value) {
        const { min, max, range } = this.config;
        
        // Clamp value
        value = Math.max(min, Math.min(max, value));

        // For range slider, ensure handles don't cross
        if (range) {
            if (index === 0 && value > this.values[1]) {
                value = this.values[1];
            } else if (index === 1 && value < this.values[0]) {
                value = this.values[0];
            }
        }

        this.values[index] = value;
        this.updateUI();
        this.config.onChange(this.getValues());
    }

    updateUI() {
        const { min, max, range, formatValue, showFill } = this.config;
        const totalRange = max - min;
        const handleOffset = 10; // Half of handle width (w-5 = 20px / 2 = 10px)

        if (range) {
            // Dual handle
            const leftPercent = ((this.values[0] - min) / totalRange) * 100;
            const rightPercent = ((this.values[1] - min) / totalRange) * 100;
            
            console.log('updateUI - values:', this.values, 'min:', min, 'max:', max, 'leftPercent:', leftPercent, 'rightPercent:', rightPercent);
            
            this.handles[0].style.left = `calc(${leftPercent}% - ${handleOffset}px)`;
            this.handles[1].style.left = `calc(${rightPercent}% - ${handleOffset}px)`;
            
            if (showFill && this.fill) {
                this.fill.style.left = `${leftPercent}%`;
                this.fill.style.width = `${rightPercent - leftPercent}%`;
                console.log('Fill set - left:', this.fill.style.left, 'width:', this.fill.style.width);
            }

            if (this.tooltips[0]) this.tooltips[0].textContent = formatValue(this.values[0]);
            if (this.tooltips[1]) this.tooltips[1].textContent = formatValue(this.values[1]);
            
            if (this.valueDisplays.min) this.valueDisplays.min.textContent = formatValue(this.values[0]);
            if (this.valueDisplays.max) this.valueDisplays.max.textContent = formatValue(this.values[1]);

            if (this.inputs[0]) this.inputs[0].value = this.values[0];
            if (this.inputs[1]) this.inputs[1].value = this.values[1];
        } else {
            // Single handle
            const percent = ((this.values[0] - min) / totalRange) * 100;
            
            this.handles[0].style.left = `calc(${percent}% - ${handleOffset}px)`;
            
            if (showFill && this.fill) {
                this.fill.style.left = '0%';
                this.fill.style.width = `${percent}%`;
            }

            if (this.tooltips[0]) this.tooltips[0].textContent = formatValue(this.values[0]);
            if (this.valueDisplays.min) this.valueDisplays.min.textContent = formatValue(this.values[0]);
            if (this.inputs[0]) this.inputs[0].value = this.values[0];
        }
    }

    showTooltip(index) {
        if (this.tooltips[index]) {
            this.tooltips[index].classList.remove('opacity-0');
            this.tooltips[index].classList.add('opacity-100');
        }
    }

    hideTooltip(index) {
        if (this.tooltips[index]) {
            this.tooltips[index].classList.remove('opacity-100');
            this.tooltips[index].classList.add('opacity-0');
        }
    }

    // Public API
    getValues() {
        return this.config.range ? [...this.values] : this.values[0];
    }

    setValues(values) {
        if (this.config.range && Array.isArray(values)) {
            this.values = [
                Math.max(this.config.min, Math.min(values[0], this.config.max)),
                Math.max(this.config.min, Math.min(values[1], this.config.max))
            ];
        } else {
            const val = Array.isArray(values) ? values[0] : values;
            this.values = [Math.max(this.config.min, Math.min(val, this.config.max))];
        }
        this.updateUI();
    }

    setMin(min) {
        this.config.min = min;
        this.updateUI();
    }

    setMax(max) {
        this.config.max = max;
        this.updateUI();
    }

    enable() {
        this.config.disabled = false;
        this.root.classList.remove('opacity-50', 'pointer-events-none');
    }

    disable() {
        this.config.disabled = true;
        this.root.classList.add('opacity-50', 'pointer-events-none');
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RangeSlider;
}
