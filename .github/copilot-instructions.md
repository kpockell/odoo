# Copilot instructions for Odoo

## Build, test, and lint commands

- Install Python dependencies with `pip install -r requirements.txt`. The repository includes a simple local startup script in `start.ps1` that activates `.venv`, installs `requirements.txt`, and runs `python odoo-bin -c odoo.conf`.
- Start the server with `python odoo-bin -c odoo.conf`. `odoo-bin` is the main entry point and dispatches into `odoo.cli.main()`.
- Odoo tests run through the server against a PostgreSQL database, not through `pytest`.
- Run tests for a module during install with `python odoo-bin -d <db> -i <module> --test-enable --stop-after-init`.
- Run tests for an already-installed module during update with `python odoo-bin -d <db> -u <module> --test-enable --stop-after-init`.
- Run a single test class or method with `python odoo-bin -d <db> -i <module> --test-enable --test-tags /<module>:<TestClass>[.<test_method>] --stop-after-init`.
- Run a standalone Python test file with `python odoo-bin -d <db> --test-file=<path-to-test-file> --stop-after-init`.
- Test selection is controlled by `--test-tags`; the built-in format is `[-][tag][/module][:class][.method][[params]]`. Common repo tags include `standard`, `at_install`, `post_install`, and custom tags such as `post_install_l10n`.
- There is no single top-level lint command in the repo. The main lint checks are implemented as tests in `odoo.addons.test_lint`.
- Run the lint addon checks with `python odoo-bin -d <db> -i test_lint --test-enable --stop-after-init`.
- JS linting in `test_lint` shells out to `eslint`; Python linting shells out to `pylint` with Odoo-specific checkers. `setup.cfg` also contains a `flake8` configuration, primarily for repository/doc-style validation.

## High-level architecture

- `odoo-bin` starts the CLI, and the default server path goes through `odoo.cli.server` into `odoo.service.server.start()`.
- `odoo` is a namespace package. Addons are discovered from `odoo/addons`, configured `addons_path` entries, and the addons data directory. The loader wires those locations into `odoo.addons.__path__`, so Copilot changes should respect addon boundaries rather than assuming everything lives under one tree.
- The server is database-centric: each database has its own `Registry` instance (`odoo.modules.registry.Registry`). Loading or updating modules rebuilds part or all of that registry, then initializes model classes, schema, data files, demo data, translations, and hooks.
- Addon installation/update flows through `odoo.modules.loading`. Manifest files (`__manifest__.py`) declare dependencies, ordered `data`/`demo` files, hooks, and web `assets`; those declarations drive module loading order and what XML/CSV/SQL files are imported.
- The ORM lives in `odoo.models`, `odoo.fields`, and `odoo.api`. Business code normally works through `self.env[...]`, `env.ref(...)`, field descriptors, and API decorators rather than raw SQL or hand-built service layers.
- The HTTP stack is in `odoo.http`. Requests are dispatched through `ir.http`, then controller methods decorated with `@http.route`. Web controllers generally use `request.env`, `request.session`, `request.render`, and `request.redirect`; for `auth="none"` routes, code often has to restore or update the request environment explicitly.
- The web client is addon-driven. The `web` addon manifest declares large asset bundles, and frontend behavior is assembled from manifest `assets` entries plus XML templates and controllers rather than a separate root frontend app build.

## Key conventions

- Distinguish core framework code in `odoo\` from business addons in both `odoo\addons\` and top-level `addons\`. When extending business behavior, look for an existing addon model/controller/view first instead of modifying framework internals.
- New addons and built-in addons are manifest-first. If you add XML views, security files, demo data, reports, or assets, they must be listed in `__manifest__.py` in load order or Odoo will not import them.
- Addon Python packages are import-driven as well: if you add a model, controller, wizard, or report module, update the relevant package `__init__.py` so the loader actually imports it.
- Model extension is usually additive through `_inherit = 'existing.model'`; new models use `_name`, and reusable behavior often uses `models.AbstractModel` mixins. Search for `_inherit` before creating parallel logic.
- View/UI behavior is often defined through XML records plus Python helpers, not only Python code. Changes to fields, menus, actions, reports, or form layouts usually involve both model code and manifest-listed XML under `views`, `security`, `wizard`, or `report`.
- Asset bundles use manifest `assets` mappings and bundle naming like `<module>.assets_<name>`. The `web` addon also uses bundle operations such as `('include', ...)` and `('remove', ...)`; follow that pattern instead of inventing ad hoc asset loading.
- Tests are standard `unittest`-style classes built on `odoo.tests.common` cases. Tagging matters: many integration tests are marked `@tagged('post_install', '-at_install')`, so picking the right tag/module filter is part of running the right test.
- Linting expectations are Odoo-specific. `test_lint` runs custom pylint plugins for SQL injection, gettext formatting, and unlink override checks, so code that looks acceptable to generic Python tools may still fail repository lint tests.
- Upgrade logic is addon-local. If a change needs data or schema migration, look for or add versioned scripts under the addon `migrations\` directory instead of burying upgrade-only behavior in normal model code.
