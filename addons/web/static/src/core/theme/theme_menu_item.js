/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

/**
 * This function registers a dark mode toggle item in the user menu
 */
registry.category("user_menuitems").add("theme_toggle", env => {
    const theme = env.services.theme;
    return {
        type: "switch",
        id: "theme_toggle",
        description: _t("Dark Mode"),
        callback: () => {
            theme.toggleDarkMode();
            return theme.isDarkMode();
        },
        isChecked: () => theme.isDarkMode(),
        sequence: 35,
    };
});
