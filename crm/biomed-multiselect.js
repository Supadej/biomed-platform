/**
 * MultiSelect Component for daisyUI
 * A reusable multi-selection dropdown with search, tags, and callbacks
 * 
 * Usage:
 * const ms = new MultiSelect('containerId', {
 *     options: [{ value: '1', label: 'Option 1' }, ...],
 *     placeholder: 'Select items...',
 *     badgeClass: 'badge-primary',
 *     searchable: true,
 *     showSelectAll: true,
 *     // Custom text labels
 *     text: {
 *         search: 'ค้นหา...',
 *         selectAll: 'เลือกทั้งหมด',
 *         clearAll: 'ล้างทั้งหมด',
 *         noResults: 'ไม่พบข้อมูล'
 *     },
 *     onChange: (values) => console.log(values)
 * });
 */

class MultiSelect {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`MultiSelect: Container #${containerId} not found`);
            return;
        }

        // Default text labels
        const defaultText = {
            search: 'ค้นหา...',
            selectAll: 'เลือกทั้งหมด',
            clearAll: 'ล้างทั้งหมด',
            noResults: 'ไม่พบข้อมูล'
        };

        // Configuration with defaults
        this.config = {
            options: config.options || [],
            placeholder: config.placeholder || 'Select items...',
            badgeClass: config.badgeClass || 'badge-primary',
            checkboxClass: config.checkboxClass || 'checkbox-primary',
            searchable: config.searchable !== false,
            showSelectAll: config.showSelectAll !== false,
            showCount: config.showCount || false,
            maxDisplay: config.maxDisplay || null, // null = show all tags
            maxSelect: config.maxSelect || null, // null = no limit on selections
            text: { ...defaultText, ...(config.text || {}) }, // Merge custom text with defaults
            onChange: config.onChange || (() => {}),
            onOpen: config.onOpen || (() => {}),
            onClose: config.onClose || (() => {}),
            onMaxReached: config.onMaxReached || (() => {})
        };

        this.selected = new Map();
        this.isOpen = false;

        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="multi-select" data-ms-root style="position: relative; width: 100%; display: block;">
                <div class="multi-select-trigger select select-bordered" data-ms-trigger style="display: flex; align-items: center; width: 100%; min-height: 3rem; height: auto; padding: 0.5rem 0.75rem; cursor: pointer; box-sizing: border-box;">
                    <div style="flex: 1; display: flex; flex-wrap: wrap; gap: 0.375rem; align-items: center; min-height: 1.5rem;" data-ms-tags>
                        <span class="text-base-content/50" style="font-size: 0.875rem;">${this.config.placeholder}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0;">
                        ${this.config.showCount ? '<span class="badge badge-neutral badge-sm" data-ms-count>0</span>' : ''}
                        <i class="fas fa-chevron-down text-base-content/50" style="transition: transform 0.2s;" data-ms-arrow></i>
                    </div>
                </div>
                <div class="multi-select-dropdown hidden bg-base-100" data-ms-dropdown style="position: absolute; top: 100%; left: 0; right: 0; width: 100%; margin-top: 0.25rem; border: 1px solid oklch(var(--b3)); border-radius: 0.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.2); z-index: 99999; overflow: hidden;">
                    ${this.config.searchable || this.config.showSelectAll ? `
                        <div class="bg-base-200" style="padding: 0.5rem; border-bottom: 1px solid oklch(var(--b3)); display: flex; align-items: center; gap: 0.5rem;">
                            ${this.config.searchable ? `<input type="text" placeholder="${this.config.text.search}" class="input input-sm input-bordered bg-base-100" style="flex: 1;" data-ms-search>` : '<div style="flex: 1;"></div>'}
                            ${this.config.showSelectAll ? `
                                <div style="display: flex; align-items: center; gap: 0.25rem; flex-shrink: 0;">
                                    <button class="btn btn-xs btn-ghost" title="${this.config.text.selectAll}" data-ms-select-all>
                                        <i class="fas fa-check-double"></i>
                                    </button>
                                    <button class="btn btn-xs btn-ghost" title="${this.config.text.clearAll}" data-ms-clear-all>
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                    <div class="bg-base-100" style="padding: 0.5rem; max-height: 240px; overflow-y: auto;" data-ms-options>
                        ${this.renderOptions()}
                    </div>
                </div>
            </div>
        `;

        // Store references
        this.root = this.container.querySelector('[data-ms-root]');
        this.trigger = this.container.querySelector('[data-ms-trigger]');
        this.tagsContainer = this.container.querySelector('[data-ms-tags]');
        this.dropdown = this.container.querySelector('[data-ms-dropdown]');
        this.optionsList = this.container.querySelector('[data-ms-options]');
        this.searchInput = this.container.querySelector('[data-ms-search]');
        this.arrow = this.container.querySelector('[data-ms-arrow]');
        this.countBadge = this.container.querySelector('[data-ms-count]');
    }

    renderOptions() {
        return this.config.options.map(opt => `
            <div class="multi-select-item bg-base-100 hover:bg-base-200" data-value="${String(opt.value)}" data-label="${opt.label}" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.625rem; border-radius: 0.375rem; cursor: pointer;">
                <input type="checkbox" class="checkbox checkbox-sm ${this.config.checkboxClass}">
                <span class="text-base-content" style="flex: 1; font-size: 0.875rem; user-select: none;">${opt.label}</span>
                ${opt.badge ? `<span class="badge badge-sm badge-ghost">${opt.badge}</span>` : ''}
            </div>
        `).join('');
    }

    bindEvents() {
        // Toggle dropdown
        this.trigger.addEventListener('click', (e) => {
            if (!e.target.closest('.tag-remove')) {
                this.toggle();
            }
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });

        // Option selection
        this.optionsList.addEventListener('click', (e) => {
            const item = e.target.closest('.multi-select-item');
            if (item) {
                e.preventDefault();
                e.stopPropagation();
                this.toggleOption(item.dataset.value, item.dataset.label);
            }
        });

        // Search
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.filter(e.target.value);
            });
            this.searchInput.addEventListener('click', (e) => e.stopPropagation());
        }

        // Select All
        const selectAllBtn = this.container.querySelector('[data-ms-select-all]');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectAll();
            });
        }

        // Clear All
        const clearAllBtn = this.container.querySelector('[data-ms-clear-all]');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clearAll();
            });
        }
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.dropdown.classList.remove('hidden');
        this.arrow.classList.add('rotate-180');
        if (this.searchInput) {
            this.searchInput.value = '';
            this.filter('');
            this.searchInput.focus();
        }
        this.config.onOpen();
    }

    close() {
        this.isOpen = false;
        this.dropdown.classList.add('hidden');
        this.arrow.classList.remove('rotate-180');
        this.config.onClose();
    }

    toggleOption(value, label) {
        // Ensure value is string for consistent comparison
        value = String(value);
        
        if (this.selected.has(value)) {
            this.selected.delete(value);
        } else {
            // Check maxSelect limit
            if (this.config.maxSelect && this.selected.size >= this.config.maxSelect) {
                // Shake the count badge
                if (this.countBadge) {
                    this.countBadge.classList.add('animate-shake');
                    setTimeout(() => {
                        this.countBadge.classList.remove('animate-shake');
                    }, 500);
                }
                this.config.onMaxReached(this.config.maxSelect);
                return;
            }
            this.selected.set(value, label);
        }
        this.updateUI();
        this.config.onChange(this.getValues());
    }

    updateUI() {
        // Update checkboxes
        this.optionsList.querySelectorAll('.multi-select-item').forEach(item => {
            const checkbox = item.querySelector('input[type="checkbox"]');
            // Ensure comparison is string to string
            const isSelected = this.selected.has(String(item.dataset.value));
            checkbox.checked = isSelected;
            item.classList.toggle('bg-primary/10', isSelected);
        });

        // Update tags
        this.updateTags();

        // Update count
        if (this.countBadge) {
            this.countBadge.textContent = this.selected.size;
            
            // Change color when at max
            if (this.config.maxSelect && this.selected.size >= this.config.maxSelect) {
                this.countBadge.classList.remove('badge-neutral');
                this.countBadge.classList.add('badge-error');
            } else {
                this.countBadge.classList.remove('badge-error');
                this.countBadge.classList.add('badge-neutral');
            }
        }
    }

    updateTags() {
        if (this.selected.size === 0) {
            this.tagsContainer.innerHTML = `<span class="text-base-content/50" style="font-size: 0.875rem;">${this.config.placeholder}</span>`;
            return;
        }

        const entries = Array.from(this.selected.entries());
        const displayEntries = this.config.maxDisplay 
            ? entries.slice(0, this.config.maxDisplay)
            : entries;
        const remaining = entries.length - displayEntries.length;

        this.tagsContainer.innerHTML = displayEntries.map(([value, label]) => `
            <span class="badge ${this.config.badgeClass}" style="display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.5rem 0.75rem; font-size: 0.75rem; font-weight: 500;">
                <span style="max-width: 8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${label}</span>
                <button type="button" class="tag-remove" data-value="${value}" style="opacity: 0.8; margin-left: 0.25rem; cursor: pointer; background: none; border: none; padding: 0; color: inherit;">
                    <i class="fas fa-times" style="font-size: 0.625rem;"></i>
                </button>
            </span>
        `).join('') + (remaining > 0 ? `<span class="badge badge-ghost" style="padding: 0.5rem 0.75rem; font-size: 0.75rem;">+${remaining}</span>` : '');

        // Bind remove buttons
        this.tagsContainer.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const value = btn.dataset.value;
                this.selected.delete(value);
                this.updateUI();
                this.config.onChange(this.getValues());
            });
        });
    }

    filter(searchText) {
        const search = searchText.toLowerCase();
        this.optionsList.querySelectorAll('.multi-select-item').forEach(item => {
            const label = item.dataset.label.toLowerCase();
            const value = item.dataset.value.toLowerCase();
            const matches = label.includes(search) || value.includes(search);
            item.style.display = matches ? '' : 'none';
        });
    }

    selectAll() {
        // Respect maxSelect limit
        const limit = this.config.maxSelect || this.config.options.length;
        let count = 0;
        this.config.options.forEach(opt => {
            if (count < limit) {
                // Store value as string for consistency
                this.selected.set(String(opt.value), opt.label);
                count++;
            }
        });
        this.updateUI();
        this.config.onChange(this.getValues());
    }

    clearAll() {
        this.selected.clear();
        this.updateUI();
        this.config.onChange(this.getValues());
    }

    // Public API
    getValues() {
        return Array.from(this.selected.keys());
    }

    getSelected() {
        return Array.from(this.selected.entries()).map(([value, label]) => ({ value, label }));
    }

    setValues(values) {
        this.selected.clear();
        values.forEach(value => {
            // Convert to string for comparison
            const valueStr = String(value);
            const opt = this.config.options.find(o => String(o.value) === valueStr);
            if (opt) {
                this.selected.set(valueStr, opt.label);
            }
        });
        this.updateUI();
    }

    setOptions(options) {
        this.config.options = options;
        this.selected.clear();
        this.optionsList.innerHTML = this.renderOptions();
        this.updateUI();
        this.bindOptionEvents();
    }

    bindOptionEvents() {
        this.optionsList.addEventListener('click', (e) => {
            const item = e.target.closest('.multi-select-item');
            if (item) {
                e.preventDefault();
                e.stopPropagation();
                this.toggleOption(item.dataset.value, item.dataset.label);
            }
        });
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MultiSelect;
}
