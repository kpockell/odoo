import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";

/** Odoo Theme Service: Dark Mode Toggle */

const DARK_MODE_STORAGE_KEY = "odoo_dark_mode";

export const themeService = {
  // No dependencies - this service should load early
  darkMode: false,

  start() {
    // Add no-transition class to avoid transition flicker on page load
    document.documentElement.classList.add("no-transition");
    
    // Check if dark mode was previously enabled
    const savedDarkMode = browser.localStorage.getItem(DARK_MODE_STORAGE_KEY);
    if (savedDarkMode === "true") {
      this.darkMode = true;
      // Apply to both HTML and BODY elements for maximum CSS variable coverage
      document.documentElement.classList.add("o-theme-dark");
      document.body.classList.add("o-theme-dark");
    } else {
      // Ensure dark mode classes are removed
      document.documentElement.classList.remove("o-theme-dark");
      document.body.classList.remove("o-theme-dark");
    }
    
    // Remove no-transition class after initial render
    setTimeout(() => {
      document.documentElement.classList.remove("no-transition");
      
      // Force style recalculation to ensure variables are applied
      if (this.darkMode) {
        const style = document.documentElement.style;
        style.display = 'none';
        // Force a reflow
        void document.documentElement.offsetHeight;
        style.display = '';
      }
    }, 100);
    
    return this;
  },

  toggleDarkMode() {
    this.darkMode = !this.darkMode;
    // Apply class to HTML element for maximum CSS variable scope
    document.documentElement.classList.toggle("o-theme-dark", this.darkMode);
    // Also apply to body for legacy code
    document.body.classList.toggle("o-theme-dark", this.darkMode);
    browser.localStorage.setItem(DARK_MODE_STORAGE_KEY, this.darkMode);
    
    // Force a small delay to ensure CSS variables are recomputed
    setTimeout(() => {
      // Dispatch a custom event that other components can listen for
      document.dispatchEvent(new CustomEvent('themeChanged', { 
        detail: { isDarkMode: this.darkMode } 
      }));
    }, 50);
  },

  isDarkMode() {
    return this.darkMode;
  },
};

// Register the service in Odoo's service registry
registry.category("services").add("theme", themeService);

// CSS for dark mode is defined in the theme's stylesheet
// .o-theme-dark { background: #222; color: #eee; }