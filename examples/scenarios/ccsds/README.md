# CCSDS DTN Reference Scenarios

Vendored copy of the [CCSDS/ESA DTN Reference Scenarios](https://github.com/esa/ccsds-dtn-reference-scenarios)
(release branch, commit `4b15bff`), v1.0 of each scenario.

- `lunar-communication/` — Lunar Communication with Relays, Gateway and User
  segments
- `mars-communication/` — Mars Relay communication with a deep space backbone
- `low-earth-orbit/` — Earth observation from LEO with downlink passes

Each scenario directory contains:

- `nodes.json` — network nodes with labels and `ipn:` endpoint identifiers
- `planned_contacts.csv` — planned contact plan used as routing knowledge
  (fixed `0,-1` links are always-on)
- `actual_contacts.csv` — actual contacts (after applying an error model),
  used as the data plane; may interrupt, shorten or drop planned contacts
- `traffic.json` — application traffic flows
- `policy.json` — flow-to-link restrictions (not yet supported by the
  scenariorunner)
- `visibility.csv` — asset visibilities the contact plan was derived from
  (not used for simulation)
- `*.adoc` — scenario documentation
- `CHANGELOG.md`

Run a scenario with:

```bash
scenariorunner --scenario-dir examples/scenarios/ccsds/lunar-communication/v1.0 -r StaticRouter -t 86400
```

The scenario files (`nodes.json`, `traffic.json`, planned/actual contacts
CSVs) are the canonical scenario input format for PONS' `scenariorunner`.

The original PDFs and images of the upstream repository are not included here.
The scenarios are licensed CC-BY-4.0 by the Consultative Committee for Space
Data Systems (CCSDS), see `LICENSE` in this directory.
