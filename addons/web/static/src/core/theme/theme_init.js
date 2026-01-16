/** @odoo-module **/

import { registry } from "@web/core/registry";
import registerThemeMenuItem from "@web/core/theme/theme_menu_item";
import { startService } from "@web/core/service_hook";
import { themeService } from "@web/core/theme/theme";

// This ensures the theme service is loaded and started
startService(themeService);

// Add to main services initialization
registry.category("main_components").add("theme_service_loader", {
    Component: class ThemeLoader extends null {
        setup() {
            // This is just a placeholder component to ensure the theme service is started
        }
    },
});
