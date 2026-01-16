/** @odoo-module **/

import { Component, useState, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ThemeToggle extends Component {
    static template = "web.ThemeToggle";
    static props = {};

    setup() {
        this.theme = useService("theme");
        this.state = useState({
            isDarkMode: this.theme.isDarkMode(),
        });
    }

    toggleDarkMode() {
        this.theme.toggleDarkMode();
        this.state.isDarkMode = this.theme.isDarkMode();
    }
}
