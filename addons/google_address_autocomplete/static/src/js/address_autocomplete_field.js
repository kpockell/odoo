/** @odoo-module **/

import { useChildRef, useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { charField, CharField } from "@web/views/fields/char/char_field";
import { useInputField } from "@web/views/fields/input_field_hook";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { KeepLast } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";

/**
 * Generate a v4 UUID to use as a Google Places session token.
 * Session tokens group autocomplete + place-details requests into a single
 * billable unit.  A new token should be generated after each complete session
 * (i.e. after the user has selected a suggestion).
 */
function generateSessionToken() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
}

export class AddressAutocompleteField extends CharField {
    static template = "google_address_autocomplete.AddressAutocompleteField";
    static components = {
        ...CharField.components,
        AutoComplete,
    };

    setup() {
        super.setup();

        this.notification = useService("notification");
        this.inputRef = useChildRef();
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            parse: (v) => this.parse(v),
            ref: this.inputRef,
        });

        this._keepLast = new KeepLast();
        this._sessionToken = generateSessionToken();
    }

    // -----------------------------------------------------------------
    // AutoComplete sources
    // -----------------------------------------------------------------

    get sources() {
        return [
            {
                options: async (request) => {
                    if (!request || request.length < 3) {
                        return [];
                    }
                    let result;
                    try {
                        result = await this._keepLast.add(
                            rpc("/google_address_autocomplete/autocomplete", {
                                input: request,
                                session_token: this._sessionToken,
                            })
                        );
                    } catch {
                        // KeepLast cancelled or network failure – silently return empty
                        return [];
                    }
                    if (!result || result.error === "no_api_key") {
                        return [];
                    }
                    if (result.error) {
                        return [];
                    }
                    return result.suggestions || [];
                },
                optionTemplate: "google_address_autocomplete.AddressOption",
                placeholder: "Searching addresses\u2026",
            },
        ];
    }

    // -----------------------------------------------------------------
    // Selection handler
    // -----------------------------------------------------------------

    async onSelect(option) {
        const placeId = option.place_id;
        if (!placeId) {
            return;
        }

        let details;
        try {
            details = await rpc("/google_address_autocomplete/place_details", {
                place_id: placeId,
                session_token: this._sessionToken,
            });
        } catch {
            return;
        }

        // Rotate the session token after each complete autocomplete session
        this._sessionToken = generateSessionToken();

        if (!details || details.error) {
            return;
        }

        const update = {};
        // Only include non-empty values so we never blank out a field the
        // user has already filled in manually.
        // Always write to 'street' regardless of which field the widget is on.
        if (details.name) {
            update.name = details.name;
        }
        if (details.street) {
            update.street = details.street;
        }
        if (details.city) {
            update.city = details.city;
        }
        if (details.zip) {
            update.zip = details.zip;
        }
        if (details.state_id) {
            update.state_id = details.state_id;
        }
        if (details.country_id) {
            update.country_id = details.country_id;
        }

        await this.props.record.update(update);
    }
}

export const addressAutocompleteField = {
    ...charField,
    component: AddressAutocompleteField,
};

// Register our new address autocomplete widget.
registry.category("fields").add("address_autocomplete", addressAutocompleteField);
