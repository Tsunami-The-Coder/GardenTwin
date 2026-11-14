# Shared API planning template

Owners: both. Fill this in together; these are decisions to make, not an implemented contract.

## Connection

- Backend framework: [Ayaan chooses]
- Frontend framework/tool: [you choose]
- Local backend address and port: [agree]
- How the frontend reaches Ayaan's local backend during integration: [agree; localhost on two computers refers to two different machines]
- Run commands: [Ayaan adds after setup]

## Garden inputs

| Input | Format / units | Default or allowed values | Backend support |
| --- | --- | --- | --- |
| Location | [coordinates or place ID] | Edison, NJ pilot | [TBD] |
| Plant | [identifier] | Tomato pilot | [TBD] |
| Planting date | [agree date format and seed/transplant meaning] | [TBD] | [TBD] |
| Simulation duration | [days or end date] | [TBD] | [TBD] |
| Soil conditions | [properties and units] | [TBD] | [TBD] |
| Garden area | [units] | [TBD] | [TBD] |
| Watering schedule | [amount, frequency and units] | [TBD] | [TBD] |
| Fertilizer usage | [type, amount, timing and units] | [TBD] | [TBD] |

## Daily timeline outputs

Agree on which of these are available for the first version:

- Date / simulation day.
- Growth stage or growth indicator, including how it is calculated.
- Weather: rainfall, temperature and heat/drought indicators.
- Soil moisture with units and definition.
- Nutrient availability, if modeled.
- Plant stress/health indicator with definition and limitations.
- Irrigation recommendation, amount and explanation.
- Fertilizer recommendation, only if supported by the selected model.

## Strategy comparison outputs

- Strategy names and identical comparison conditions: [TBD]
- Total irrigation and units: [TBD]
- Stress metric and definition: [TBD]
- Estimated productivity, if supported: [TBD]
- Whether each result is observed, predicted, simulated or illustrative: [TBD]

## Interface details

- Endpoint names, methods, request fields and response fields: [Ayaan proposes]
- Error format and loading behavior: [agree]
- Unsupported or missing outputs: [agree; avoid inventing values]
- Example request / response files: [create together once the schema is agreed]
