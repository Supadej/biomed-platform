/**
 * DaisyUI Date Range Picker Library
 * A customizable date range picker component built with DaisyUI styling
 * 
 * @version 1.0.0
 * @author Biomed2.0 Team
 * @license MIT
 */

(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.DaisyDateRangePicker = factory());
})(this, (function () {
    'use strict';

    // ============================================================================
    // DEFAULT CONFIGURATION
    // ============================================================================
    const DEFAULT_OPTIONS = {
        // Appearance
        theme: 'default', // 'default', 'primary', 'secondary', 'accent', 'neutral'
        size: 'md', // 'xs', 'sm', 'md', 'lg', 'xl'
        rounded: true,
        bordered: true,
        
        // Behavior
        autoClose: true,
        closeOnSelect: false,
        showPresets: true,
        showTimePicker: false,
        singleDateMode: false,
        
        // Date constraints
        minDate: null,
        maxDate: null,
        disabledDates: [],
        disabledDaysOfWeek: [],
        
        // Localization
        locale: 'th-TH',
        firstDayOfWeek: 0, // 0 = Sunday, 1 = Monday
        dateFormat: 'DD/MM/YYYY',
        monthNames: ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 
                     'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'],
        monthNamesShort: ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 
                          'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'],
        dayNames: ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'],
        dayNamesShort: ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'],
        
        // Preset ranges
        presets: [
            { label: 'วันนี้', getValue: () => ({ start: new Date(), end: new Date() }) },
            { label: 'เมื่อวาน', getValue: () => {
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                return { start: yesterday, end: yesterday };
            }},
            { label: '7 วันล่าสุด', getValue: () => {
                const end = new Date();
                const start = new Date();
                start.setDate(start.getDate() - 6);
                return { start, end };
            }},
            { label: '30 วันล่าสุด', getValue: () => {
                const end = new Date();
                const start = new Date();
                start.setDate(start.getDate() - 29);
                return { start, end };
            }},
            { label: 'เดือนนี้', getValue: () => {
                const now = new Date();
                const start = new Date(now.getFullYear(), now.getMonth(), 1);
                const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                return { start, end };
            }},
            { label: 'เดือนที่แล้ว', getValue: () => {
                const now = new Date();
                const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                const end = new Date(now.getFullYear(), now.getMonth(), 0);
                return { start, end };
            }},
            { label: 'ปีนี้', getValue: () => {
                const now = new Date();
                const start = new Date(now.getFullYear(), 0, 1);
                const end = new Date(now.getFullYear(), 11, 31);
                return { start, end };
            }}
        ],
        
        // Callbacks
        onChange: null,
        onOpen: null,
        onClose: null,
        onApply: null,
        onClear: null,
        
        // Labels
        labels: {
            placeholder: 'เลือกช่วงวันที่',
            startPlaceholder: 'วันเริ่มต้น',
            endPlaceholder: 'วันสิ้นสุด',
            apply: 'ตกลง',
            cancel: 'ยกเลิก',
            clear: 'ล้าง',
            presets: 'ช่วงที่กำหนด'
        }
    };

    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================
    const Utils = {
        /**
         * Generate unique ID
         */
        generateId() {
            return 'drp_' + Math.random().toString(36).substr(2, 9);
        },

        /**
         * Deep merge objects
         */
        deepMerge(target, source) {
            const result = { ...target };
            for (const key in source) {
                if (source[key] instanceof Object && !Array.isArray(source[key])) {
                    result[key] = this.deepMerge(result[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
            return result;
        },

        /**
         * Format date to string
         */
        formatDate(date, format, monthNames) {
            if (!date) return '';
            
            const d = new Date(date);
            const day = d.getDate().toString().padStart(2, '0');
            const month = (d.getMonth() + 1).toString().padStart(2, '0');
            const year = d.getFullYear();
            const yearBE = year + 543;
            
            return format
                .replace('DD', day)
                .replace('MM', month)
                .replace('MMMM', monthNames[d.getMonth()])
                .replace('YYYY', year)
                .replace('BBBB', yearBE);
        },

        /**
         * Parse date string
         */
        parseDate(dateStr, format) {
            if (!dateStr) return null;
            
            const parts = dateStr.split(/[\/\-\.]/);
            const formatParts = format.split(/[\/\-\.]/);
            
            let day, month, year;
            
            formatParts.forEach((part, index) => {
                if (part === 'DD') day = parseInt(parts[index]);
                if (part === 'MM') month = parseInt(parts[index]) - 1;
                if (part === 'YYYY') year = parseInt(parts[index]);
                if (part === 'BBBB') year = parseInt(parts[index]) - 543;
            });
            
            return new Date(year, month, day);
        },

        /**
         * Check if two dates are the same day
         */
        isSameDay(date1, date2) {
            if (!date1 || !date2) return false;
            return date1.getDate() === date2.getDate() &&
                   date1.getMonth() === date2.getMonth() &&
                   date1.getFullYear() === date2.getFullYear();
        },

        /**
         * Check if date is between two dates
         */
        isDateBetween(date, start, end) {
            if (!date || !start || !end) return false;
            const d = new Date(date).setHours(0, 0, 0, 0);
            const s = new Date(start).setHours(0, 0, 0, 0);
            const e = new Date(end).setHours(0, 0, 0, 0);
            return d >= s && d <= e;
        },

        /**
         * Check if date is disabled
         */
        isDateDisabled(date, options) {
            const d = new Date(date).setHours(0, 0, 0, 0);
            
            // Check min date
            if (options.minDate && d < new Date(options.minDate).setHours(0, 0, 0, 0)) {
                return true;
            }
            
            // Check max date
            if (options.maxDate && d > new Date(options.maxDate).setHours(0, 0, 0, 0)) {
                return true;
            }
            
            // Check disabled dates
            if (options.disabledDates.some(dd => this.isSameDay(new Date(dd), date))) {
                return true;
            }
            
            // Check disabled days of week
            if (options.disabledDaysOfWeek.includes(date.getDay())) {
                return true;
            }
            
            return false;
        },

        /**
         * Get days in month
         */
        getDaysInMonth(year, month) {
            return new Date(year, month + 1, 0).getDate();
        },

        /**
         * Get first day of month
         */
        getFirstDayOfMonth(year, month) {
            return new Date(year, month, 1).getDay();
        },

        /**
         * Create element with classes
         */
        createElement(tag, classes = [], attributes = {}) {
            const el = document.createElement(tag);
            if (classes.length) el.className = classes.join(' ');
            Object.entries(attributes).forEach(([key, value]) => {
                el.setAttribute(key, value);
            });
            return el;
        }
    };

    // ============================================================================
    // MAIN CLASS
    // ============================================================================
    class DaisyDateRangePicker {
        constructor(element, options = {}) {
            // Handle selector or element
            this.element = typeof element === 'string' 
                ? document.querySelector(element) 
                : element;
            
            if (!this.element) {
                throw new Error('DaisyDateRangePicker: Element not found');
            }
            
            // Merge options
            this.options = Utils.deepMerge(DEFAULT_OPTIONS, options);
            
            // State
            this.state = {
                isOpen: false,
                startDate: null,
                endDate: null,
                hoverDate: null,
                currentMonth: new Date().getMonth(),
                currentYear: new Date().getFullYear(),
                selectingStart: true
            };
            
            // Generate unique IDs
            this.id = Utils.generateId();
            
            // Initialize
            this._init();
        }

        // ========================================================================
        // INITIALIZATION
        // ========================================================================
        _init() {
            this._createElements();
            this._bindEvents();
            this._render();
        }

        _createElements() {
            // Main container
            this.container = Utils.createElement('div', ['daisy-date-range-picker', 'relative', 'inline-block']);
            this.container.id = this.id;
            
            // Input wrapper with join
            this.inputWrapper = this._createInputWrapper();
            
            // Dropdown
            this.dropdown = this._createDropdown();
            
            // Assemble
            this.container.appendChild(this.inputWrapper);
            this.container.appendChild(this.dropdown);
            
            // Insert after the original element
            this.element.parentNode.insertBefore(this.container, this.element.nextSibling);
            this.element.style.display = 'none';
        }

        _createInputWrapper() {
            const wrapper = Utils.createElement('div', ['join', 'w-full']);
            
            // Calendar icon button
            const iconBtn = Utils.createElement('button', [
                'btn', 'join-item', this._getSizeClass()
            ], { type: 'button' });
            iconBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
                </svg>
            `;
            
            // Main input (display)
            this.displayInput = Utils.createElement('input', [
                'input', 'join-item', 'flex-1',
                this._getSizeClass(),
                this.options.bordered ? 'input-bordered' : ''
            ].filter(Boolean), {
                type: 'text',
                placeholder: this.options.labels.placeholder,
                readonly: 'readonly'
            });
            
            // Clear button
            this.clearBtn = Utils.createElement('button', [
                'btn', 'join-item', 'btn-ghost', this._getSizeClass()
            ], { type: 'button' });
            this.clearBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
            `;
            this.clearBtn.style.display = 'none';
            
            wrapper.appendChild(iconBtn);
            wrapper.appendChild(this.displayInput);
            wrapper.appendChild(this.clearBtn);
            
            return wrapper;
        }

        _createDropdown() {
            const dropdown = Utils.createElement('div', [
                'dropdown-content', 'bg-base-100', 'rounded-box', 'shadow-xl',
                'border', 'border-base-300', 'p-4', 'z-50',
                'absolute', 'top-full', 'left-0', 'mt-2',
                'hidden', 'min-w-max'
            ]);
            dropdown.style.position = 'absolute';
            
            // Create dropdown content
            const content = Utils.createElement('div', ['flex', 'gap-4']);
            
            // Presets panel (left side)
            if (this.options.showPresets && !this.options.singleDateMode) {
                this.presetsPanel = this._createPresetsPanel();
                content.appendChild(this.presetsPanel);
            }
            
            // Calendars panel (right side)
            this.calendarsPanel = Utils.createElement('div', ['flex', 'flex-col', 'gap-4']);
            
            // Month navigation
            this.monthNav = this._createMonthNav();
            this.calendarsPanel.appendChild(this.monthNav);
            
            // Calendars container
            this.calendarsContainer = Utils.createElement('div', ['flex', 'gap-4']);
            
            // Left calendar
            this.leftCalendar = this._createCalendar('left');
            this.calendarsContainer.appendChild(this.leftCalendar);
            
            // Right calendar (only for date range mode)
            if (!this.options.singleDateMode) {
                this.rightCalendar = this._createCalendar('right');
                this.calendarsContainer.appendChild(this.rightCalendar);
            }
            
            this.calendarsPanel.appendChild(this.calendarsContainer);
            
            // Actions
            this.actionsPanel = this._createActionsPanel();
            this.calendarsPanel.appendChild(this.actionsPanel);
            
            content.appendChild(this.calendarsPanel);
            dropdown.appendChild(content);
            
            return dropdown;
        }

        _createPresetsPanel() {
            const panel = Utils.createElement('div', [
                'flex', 'flex-col', 'gap-1', 'border-r', 'border-base-300', 'pr-4', 'min-w-36'
            ]);
            
            const title = Utils.createElement('div', ['font-semibold', 'text-sm', 'mb-2', 'text-base-content/70']);
            title.textContent = this.options.labels.presets;
            panel.appendChild(title);
            
            this.options.presets.forEach(preset => {
                const btn = Utils.createElement('button', [
                    'btn', 'btn-ghost', 'btn-sm', 'justify-start', 'font-normal'
                ], { type: 'button' });
                btn.textContent = preset.label;
                btn.addEventListener('click', () => this._applyPreset(preset));
                panel.appendChild(btn);
            });
            
            return panel;
        }

        _createMonthNav() {
            const nav = Utils.createElement('div', ['flex', 'items-center', 'justify-between', 'mb-2']);
            
            // Previous button
            this.prevBtn = Utils.createElement('button', ['btn', 'btn-ghost', 'btn-sm', 'btn-circle'], { type: 'button' });
            this.prevBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
                </svg>
            `;
            
            // Month/Year display
            this.monthYearDisplay = Utils.createElement('div', ['flex', 'gap-4', 'font-semibold']);
            
            // Next button
            this.nextBtn = Utils.createElement('button', ['btn', 'btn-ghost', 'btn-sm', 'btn-circle'], { type: 'button' });
            this.nextBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>
            `;
            
            nav.appendChild(this.prevBtn);
            nav.appendChild(this.monthYearDisplay);
            nav.appendChild(this.nextBtn);
            
            return nav;
        }

        _createCalendar(position) {
            const calendar = Utils.createElement('div', ['calendar-grid']);
            calendar.dataset.position = position;
            return calendar;
        }

        _createActionsPanel() {
            const panel = Utils.createElement('div', [
                'flex', 'justify-between', 'items-center', 'mt-4', 'pt-4',
                'border-t', 'border-base-300'
            ]);
            
            // Selected range display
            this.rangeDisplay = Utils.createElement('div', ['text-sm', 'text-base-content/70']);
            
            // Action buttons
            const buttons = Utils.createElement('div', ['flex', 'gap-2']);
            
            this.cancelBtn = Utils.createElement('button', ['btn', 'btn-ghost', 'btn-sm'], { type: 'button' });
            this.cancelBtn.textContent = this.options.labels.cancel;
            
            this.applyBtn = Utils.createElement('button', [
                'btn', this._getThemeClass(), 'btn-sm'
            ], { type: 'button' });
            this.applyBtn.textContent = this.options.labels.apply;
            
            buttons.appendChild(this.cancelBtn);
            buttons.appendChild(this.applyBtn);
            
            panel.appendChild(this.rangeDisplay);
            panel.appendChild(buttons);
            
            return panel;
        }

        // ========================================================================
        // EVENT BINDINGS
        // ========================================================================
        _bindEvents() {
            // Toggle dropdown
            this.inputWrapper.addEventListener('click', (e) => {
                if (e.target !== this.clearBtn && !this.clearBtn.contains(e.target)) {
                    this.toggle();
                }
            });
            
            // Clear button
            this.clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clear();
            });
            
            // Month navigation
            this.prevBtn.addEventListener('click', () => this._prevMonth());
            this.nextBtn.addEventListener('click', () => this._nextMonth());
            
            // Actions
            this.cancelBtn.addEventListener('click', () => this.close());
            this.applyBtn.addEventListener('click', () => this._apply());
            
            // Close on outside click
            document.addEventListener('click', (e) => {
                if (this.state.isOpen && !this.container.contains(e.target)) {
                    this.close();
                }
            });
            
            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (this.state.isOpen && e.key === 'Escape') {
                    this.close();
                }
            });
        }

        // ========================================================================
        // RENDERING
        // ========================================================================
        _render() {
            this._renderMonthYear();
            this._renderCalendars();
            this._renderRangeDisplay();
        }

        _renderMonthYear() {
            const leftMonth = this.state.currentMonth;
            const leftYear = this.state.currentYear;
            const rightMonth = (leftMonth + 1) % 12;
            const rightYear = leftMonth === 11 ? leftYear + 1 : leftYear;
            
            let display = `${this.options.monthNames[leftMonth]} ${leftYear}`;
            if (!this.options.singleDateMode) {
                display += ` — ${this.options.monthNames[rightMonth]} ${rightYear}`;
            }
            
            this.monthYearDisplay.textContent = display;
        }

        _renderCalendars() {
            this._renderCalendar(this.leftCalendar, this.state.currentYear, this.state.currentMonth);
            
            if (!this.options.singleDateMode && this.rightCalendar) {
                const nextMonth = (this.state.currentMonth + 1) % 12;
                const nextYear = this.state.currentMonth === 11 ? this.state.currentYear + 1 : this.state.currentYear;
                this._renderCalendar(this.rightCalendar, nextYear, nextMonth);
            }
        }

        _renderCalendar(container, year, month) {
            container.innerHTML = '';
            
            // Day headers
            const headerRow = Utils.createElement('div', ['grid', 'grid-cols-7', 'gap-1', 'mb-2']);
            const dayNames = [...this.options.dayNamesShort];
            
            // Reorder days based on firstDayOfWeek
            for (let i = 0; i < this.options.firstDayOfWeek; i++) {
                dayNames.push(dayNames.shift());
            }
            
            dayNames.forEach(day => {
                const dayEl = Utils.createElement('div', [
                    'text-center', 'text-xs', 'font-medium', 'text-base-content/50', 'py-1'
                ]);
                dayEl.textContent = day;
                headerRow.appendChild(dayEl);
            });
            container.appendChild(headerRow);
            
            // Days grid
            const daysGrid = Utils.createElement('div', ['grid', 'grid-cols-7', 'gap-1']);
            
            const daysInMonth = Utils.getDaysInMonth(year, month);
            let firstDay = Utils.getFirstDayOfMonth(year, month) - this.options.firstDayOfWeek;
            if (firstDay < 0) firstDay += 7;
            
            // Previous month days
            const prevMonth = month === 0 ? 11 : month - 1;
            const prevYear = month === 0 ? year - 1 : year;
            const prevMonthDays = Utils.getDaysInMonth(prevYear, prevMonth);
            
            for (let i = firstDay - 1; i >= 0; i--) {
                const dayEl = this._createDayElement(prevMonthDays - i, prevYear, prevMonth, true);
                daysGrid.appendChild(dayEl);
            }
            
            // Current month days
            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month, day);
                const dayEl = this._createDayElement(day, year, month, false, date);
                daysGrid.appendChild(dayEl);
            }
            
            // Next month days
            const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
            const nextMonthDays = totalCells - (firstDay + daysInMonth);
            const nextMonth = month === 11 ? 0 : month + 1;
            const nextYear = month === 11 ? year + 1 : year;
            
            for (let day = 1; day <= nextMonthDays; day++) {
                const dayEl = this._createDayElement(day, nextYear, nextMonth, true);
                daysGrid.appendChild(dayEl);
            }
            
            container.appendChild(daysGrid);
        }

        _createDayElement(day, year, month, isOtherMonth, date = null) {
            const dayEl = Utils.createElement('button', [
                'btn', 'btn-sm', 'btn-ghost', 'w-9', 'h-9', 'p-0', 'min-h-0',
                'font-normal', 'text-sm'
            ], { type: 'button' });
            
            dayEl.textContent = day;
            
            if (isOtherMonth) {
                dayEl.classList.add('text-base-content/30');
            }
            
            if (date) {
                const isDisabled = Utils.isDateDisabled(date, this.options);
                const isStart = Utils.isSameDay(date, this.state.startDate);
                const isEnd = Utils.isSameDay(date, this.state.endDate);
                const isInRange = this.state.startDate && this.state.endDate && 
                                  Utils.isDateBetween(date, this.state.startDate, this.state.endDate);
                const isHoverRange = this.state.startDate && !this.state.endDate && this.state.hoverDate &&
                                     Utils.isDateBetween(date, this.state.startDate, this.state.hoverDate);
                const isToday = Utils.isSameDay(date, new Date());
                
                if (isDisabled) {
                    dayEl.classList.add('btn-disabled', 'text-base-content/20');
                    dayEl.disabled = true;
                } else {
                    if (isStart || isEnd) {
                        dayEl.classList.remove('btn-ghost');
                        dayEl.classList.add(this._getThemeClass());
                    } else if (isInRange || isHoverRange) {
                        dayEl.classList.add('bg-base-200');
                    }
                    
                    if (isToday && !isStart && !isEnd) {
                        dayEl.classList.add('ring-1', 'ring-primary');
                    }
                    
                    // Event handlers
                    dayEl.addEventListener('click', () => this._selectDate(date));
                    dayEl.addEventListener('mouseenter', () => this._hoverDate(date));
                }
            }
            
            return dayEl;
        }

        _renderRangeDisplay() {
            if (this.state.startDate) {
                let display = Utils.formatDate(this.state.startDate, this.options.dateFormat, this.options.monthNames);
                if (this.state.endDate && !this.options.singleDateMode) {
                    display += ' — ' + Utils.formatDate(this.state.endDate, this.options.dateFormat, this.options.monthNames);
                }
                this.rangeDisplay.textContent = display;
            } else {
                this.rangeDisplay.textContent = '';
            }
        }

        // ========================================================================
        // ACTIONS
        // ========================================================================
        _selectDate(date) {
            if (this.options.singleDateMode) {
                this.state.startDate = date;
                this.state.endDate = date;
                if (this.options.closeOnSelect) {
                    this._apply();
                }
            } else {
                if (this.state.selectingStart || !this.state.startDate) {
                    this.state.startDate = date;
                    this.state.endDate = null;
                    this.state.selectingStart = false;
                } else {
                    if (date < this.state.startDate) {
                        this.state.endDate = this.state.startDate;
                        this.state.startDate = date;
                    } else {
                        this.state.endDate = date;
                    }
                    this.state.selectingStart = true;
                    
                    if (this.options.closeOnSelect) {
                        this._apply();
                    }
                }
            }
            
            this._render();
            
            if (this.options.onChange) {
                this.options.onChange({
                    startDate: this.state.startDate,
                    endDate: this.state.endDate
                });
            }
        }

        _hoverDate(date) {
            if (!this.state.selectingStart && this.state.startDate && !this.state.endDate) {
                this.state.hoverDate = date;
                this._render();
            }
        }

        _applyPreset(preset) {
            const { start, end } = preset.getValue();
            this.state.startDate = start;
            this.state.endDate = end;
            this.state.currentMonth = start.getMonth();
            this.state.currentYear = start.getFullYear();
            this._render();
            
            if (this.options.autoClose) {
                this._apply();
            }
        }

        _prevMonth() {
            this.state.currentMonth--;
            if (this.state.currentMonth < 0) {
                this.state.currentMonth = 11;
                this.state.currentYear--;
            }
            this._render();
        }

        _nextMonth() {
            this.state.currentMonth++;
            if (this.state.currentMonth > 11) {
                this.state.currentMonth = 0;
                this.state.currentYear++;
            }
            this._render();
        }

        _apply() {
            const formatted = this._getFormattedValue();
            this.displayInput.value = formatted;
            this.element.value = formatted;
            
            // Show/hide clear button
            this.clearBtn.style.display = this.state.startDate ? 'flex' : 'none';
            
            if (this.options.onApply) {
                this.options.onApply({
                    startDate: this.state.startDate,
                    endDate: this.state.endDate,
                    formatted: formatted
                });
            }
            
            this.close();
        }

        // ========================================================================
        // PUBLIC API
        // ========================================================================
        /**
         * Open the date picker dropdown
         */
        open() {
            if (this.state.isOpen) return;
            
            this.state.isOpen = true;
            this.dropdown.classList.remove('hidden');
            
            if (this.options.onOpen) {
                this.options.onOpen();
            }
        }

        /**
         * Close the date picker dropdown
         */
        close() {
            if (!this.state.isOpen) return;
            
            this.state.isOpen = false;
            this.dropdown.classList.add('hidden');
            this.state.hoverDate = null;
            
            if (this.options.onClose) {
                this.options.onClose();
            }
        }

        /**
         * Toggle the date picker dropdown
         */
        toggle() {
            if (this.state.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }

        /**
         * Clear selected dates
         */
        clear() {
            this.state.startDate = null;
            this.state.endDate = null;
            this.state.selectingStart = true;
            this.displayInput.value = '';
            this.element.value = '';
            this.clearBtn.style.display = 'none';
            this._render();
            
            if (this.options.onClear) {
                this.options.onClear();
            }
        }

        /**
         * Set date range programmatically
         * @param {Date|string} start - Start date
         * @param {Date|string} end - End date
         */
        setDateRange(start, end) {
            this.state.startDate = start instanceof Date ? start : new Date(start);
            this.state.endDate = end instanceof Date ? end : new Date(end);
            this._render();
            this._apply();
        }

        /**
         * Get selected date range
         * @returns {Object} Object with startDate and endDate
         */
        getDateRange() {
            return {
                startDate: this.state.startDate,
                endDate: this.state.endDate
            };
        }

        /**
         * Get formatted value
         * @returns {string} Formatted date range string
         */
        _getFormattedValue() {
            if (!this.state.startDate) return '';
            
            let value = Utils.formatDate(this.state.startDate, this.options.dateFormat, this.options.monthNames);
            
            if (this.state.endDate && !this.options.singleDateMode) {
                value += ' — ' + Utils.formatDate(this.state.endDate, this.options.dateFormat, this.options.monthNames);
            }
            
            return value;
        }

        /**
         * Update options
         * @param {Object} newOptions - New options to merge
         */
        setOptions(newOptions) {
            this.options = Utils.deepMerge(this.options, newOptions);
            this._render();
        }

        /**
         * Destroy the date picker
         */
        destroy() {
            this.element.style.display = '';
            this.container.remove();
        }

        // ========================================================================
        // HELPERS
        // ========================================================================
        _getSizeClass() {
            const sizeMap = {
                'xs': 'input-xs',
                'sm': 'input-sm',
                'md': '',
                'lg': 'input-lg',
                'xl': 'input-xl'
            };
            return sizeMap[this.options.size] || '';
        }

        _getThemeClass() {
            const themeMap = {
                'default': 'btn-primary',
                'primary': 'btn-primary',
                'secondary': 'btn-secondary',
                'accent': 'btn-accent',
                'neutral': 'btn-neutral',
                'info': 'btn-info',
                'success': 'btn-success',
                'warning': 'btn-warning',
                'error': 'btn-error'
            };
            return themeMap[this.options.theme] || 'btn-primary';
        }
    }

    // ============================================================================
    // STATIC METHODS
    // ============================================================================
    /**
     * Create multiple instances from selector
     * @param {string} selector - CSS selector
     * @param {Object} options - Options
     * @returns {Array} Array of DaisyDateRangePicker instances
     */
    DaisyDateRangePicker.createAll = function(selector, options = {}) {
        const elements = document.querySelectorAll(selector);
        return Array.from(elements).map(el => new DaisyDateRangePicker(el, options));
    };

    /**
     * Get default options
     * @returns {Object} Default options object
     */
    DaisyDateRangePicker.getDefaults = function() {
        return { ...DEFAULT_OPTIONS };
    };

    /**
     * Library version
     */
    DaisyDateRangePicker.VERSION = '1.0.0';

    return DaisyDateRangePicker;

}));
