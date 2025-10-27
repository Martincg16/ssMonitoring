# Client & Billing System Implementation Plan

## 📋 Overview

This document outlines the implementation plan for adding client management and automated billing functionality to the SS Monitoring system. The implementation is divided into three phases to ensure manageable, testable increments.

---

## 🎯 Business Requirements

### Client Management
- Track both natural persons and juridical entities (companies)
- Link clients to solar projects (one client can have multiple projects)
- Store contact information and billing contacts
- Integration with external systems (HubSpot, Bubble)

### Billing System (Cero Inversión Model)
- 60-month payment contracts
- Fixed monthly amounts adjusted annually by CPI (inflation)
- Automatic calculation of monthly charges
- Export billing data to third-party payment provider
- Track production data for validation (optional)

---

## 🗺️ Implementation Phases

### **PHASE 1: Cliente (Client Management)** ✅ START HERE
**Priority:** FIRST - Foundation layer  
**Complexity:** LOW-MEDIUM  
**Dependencies:** None (standalone)  
**Time Estimate:** 1-2 hours

#### What We'll Build:
- `Cliente` model with all required fields
- Django Admin configuration for client management
- Field validations (Colombian phone numbers, email)
- Relationship to `Proyecto` model (ForeignKey)
- Migration files

#### Fields in Cliente Model:
- **Personal Information:**
  - `firstname`, `lastname`
  - `tipo_de_persona` (Natural/Jurídica)
  - `company` (optional, for juridical entities)
  - `id_colombia` (Cédula/NIT) - **UNIQUE**

- **Contact Information:**
  - `email` - **UNIQUE**
  - `phone` (Colombian format: 10 digits) - **UNIQUE**

- **Billing Contact (Cobranza):**
  - `firstname_cobranza`, `lastname_cobranza`
  - `email_cobranza` - **UNIQUE**
  - `phone_cobranza` - **UNIQUE**

- **External System IDs:**
  - `id_hs` (HubSpot) - **UNIQUE**
  - `id_bubble` (Bubble) - **UNIQUE**

- **Metadata:**
  - `fecha_creacion`, `fecha_actualizacion`

#### Deliverables:
1. ✅ Cliente model in `solarData/models.py`
2. ✅ Migration file
3. ✅ Django Admin configuration in `solarData/admin.py`
4. ✅ Updated Proyecto model with `id_cliente` field
5. ✅ Phone number validator for Colombian format
6. ✅ Test with sample data

#### Testing Checklist:
- [ ] Create natural person client
- [ ] Create juridical entity client
- [ ] Link clients to existing projects
- [ ] Verify unique constraints work (duplicate email/phone should fail)
- [ ] Test phone validation (10 digits, Colombian format)
- [ ] Verify admin interface is user-friendly

---

### **PHASE 2: Financial Contract Structure**
**Priority:** SECOND - Billing foundation  
**Complexity:** MEDIUM  
**Dependencies:** Cliente (Phase 1)  
**Time Estimate:** 2-3 hours

#### What We'll Build:
- `IndiceCPI` model (stores annual CPI/inflation data)
- `ContratoFinanciero` model (one per project)
- Django Admin configuration for both models
- Basic contract creation workflow
- Calculation methods for CPI-adjusted amounts

#### IndiceCPI Model:
- `anio` (year) - **UNIQUE**
- `porcentaje_cpi` (CPI percentage)
- `fecha_publicacion` (publication date)
- `fuente` (source, default: DANE)
- `notas` (notes)

#### ContratoFinanciero Model:
- `id_proyecto` (OneToOne with Proyecto)
- `tipo_contrato` (Cero Inversión, PPA, Arrendamiento, etc.)
- `fecha_inicio_contrato`, `fecha_fin_contrato` (auto: +60 months)
- `monto_mensual_inicial` (initial monthly amount)
- `anio_inicio_contrato` (base year for CPI calculations)
- `energia_minima_para_cobro` (optional minimum production threshold)
- `estado_contrato` (Activo, Finalizado, Suspendido, Cancelado)

#### Key Methods:
- `calcular_monto_para_mes(mes, anio)` - Calculate CPI-adjusted amount
- `get_numero_cuota(mes, anio)` - Get installment number (1-60)
- Auto-calculate end date on save

#### Deliverables:
1. ✅ IndiceCPI model
2. ✅ ContratoFinanciero model with calculation methods
3. ✅ Admin interfaces for both models
4. ✅ Migration files
5. ✅ Sample CPI data for testing (2020-2025)
6. ✅ Test contracts linked to projects

#### Testing Checklist:
- [ ] Add CPI indices for past years
- [ ] Create test contract with fecha_inicio
- [ ] Verify fecha_fin is automatically 60 months later
- [ ] Test `calcular_monto_para_mes()` manually in shell
- [ ] Verify CPI compound calculation is correct
- [ ] Test with multiple years of CPI adjustments

---

### **PHASE 3: Monthly Billing Generation & Export**
**Priority:** THIRD - Automation layer  
**Complexity:** HIGH  
**Dependencies:** Phases 1 & 2 (complete)  
**Time Estimate:** 3-4 hours

#### What We'll Build:
- `CuotaMensual` model (monthly billing records)
- Management command: `generar_cuotas_mensuales`
- Management command: `exportar_cuotas_para_cobro`
- Django Admin interface for cuotas
- Automated monthly workflow documentation

#### CuotaMensual Model:
- `id_contrato` (ForeignKey to ContratoFinanciero)
- `mes_cobro`, `anio_cobro`, `numero_cuota`
- `monto_base`, `porcentaje_cpi_acumulado`, `monto_a_cobrar`
- `energia_producida_mes` (from GeneracionEnergiaDiaria)
- `estado_cuota` (Generada, Enviada a proveedor, Exonerada, Cancelada)
- `fecha_generacion`, `fecha_envio_proveedor`

#### Management Commands:

**1. generar_cuotas_mensuales**
```powershell
python manage.py generar_cuotas_mensuales [--mes M] [--anio YYYY]
```
- Generates monthly billing for all active contracts
- Calculates CPI-adjusted amounts
- Tracks energy production
- Creates CuotaMensual records

**2. exportar_cuotas_para_cobro**
```powershell
python manage.py exportar_cuotas_para_cobro [--mes M] [--anio YYYY] [--output file.csv]
```
- Exports billing data to CSV for payment provider
- Includes client information and amounts
- Marks cuotas as "Enviada a proveedor"
- Timestamps the export

#### CSV Export Format:
```
Proyecto, Cliente_Nombre, Cliente_Apellido, Cliente_Email, Cliente_Telefono, 
Cliente_ID_Colombia, Mes, Anio, Numero_Cuota, Monto_Base, CPI_Acumulado_%, 
Monto_a_Cobrar, Energia_Producida_kWh
```

#### Deliverables:
1. ✅ CuotaMensual model
2. ✅ Migration file
3. ✅ `generar_cuotas_mensuales` management command
4. ✅ `exportar_cuotas_para_cobro` management command
5. ✅ Admin interface for reviewing cuotas
6. ✅ Documentation for monthly workflow
7. ✅ Testing with historical data

#### Testing Checklist:
- [ ] Generate cuotas for a past month with test data
- [ ] Verify CPI calculations are accurate
- [ ] Test energy production integration
- [ ] Generate cuotas for contracts with different start dates
- [ ] Test CSV export format
- [ ] Verify estado changes after export
- [ ] Test edge cases (suspended contracts, completed contracts)

---

## 🔄 Monthly Workflow (After Implementation)

### Automated Monthly Process:

1. **On the 1st of each month:**
   ```powershell
   python manage.py generar_cuotas_mensuales
   ```
   - Generates billing for previous month
   - Calculates CPI-adjusted amounts
   - Links to energy production data

2. **Review generated cuotas:**
   - Check Django Admin for any anomalies
   - Verify amounts are correct
   - Handle any exceptions (suspended contracts, etc.)

3. **Export for payment provider:**
   ```powershell
   python manage.py exportar_cuotas_para_cobro --output cuotas_YYYY_MM.csv
   ```
   - Creates CSV file
   - Send to payment provider
   - Archive for records

4. **(Optional) Set up cron job for automation**

---

## 📊 Database Schema Overview

```
Cliente (clients)
  ├── id (PK)
  ├── firstname, lastname, company
  ├── tipo_de_persona (Natural/Jurídica)
  ├── id_colombia (UNIQUE)
  ├── email (UNIQUE), phone (UNIQUE)
  └── external IDs (HubSpot, Bubble)

Proyecto (projects) - EXISTING
  ├── id (PK)
  ├── id_cliente (FK → Cliente) [NEW]
  ├── dealname, identificador_planta
  └── ... existing fields ...

ContratoFinanciero (contracts)
  ├── id (PK)
  ├── id_proyecto (OneToOne → Proyecto)
  ├── tipo_contrato, estado_contrato
  ├── fecha_inicio, fecha_fin
  ├── monto_mensual_inicial
  └── anio_inicio_contrato

IndiceCPI (inflation indices)
  ├── id (PK)
  ├── anio (UNIQUE)
  ├── porcentaje_cpi
  └── fuente, fecha_publicacion

CuotaMensual (monthly billing)
  ├── id (PK)
  ├── id_contrato (FK → ContratoFinanciero)
  ├── mes_cobro, anio_cobro
  ├── numero_cuota (1-60)
  ├── monto_base, porcentaje_cpi_acumulado
  ├── monto_a_cobrar
  ├── energia_producida_mes
  └── estado_cuota, fecha_envio_proveedor
```

---

## 📝 Notes & Considerations

### Data Migration:
- Existing projects will have `id_cliente = NULL` initially
- Clients can be added and linked to projects gradually
- Contracts can be created retroactively if needed

### CPI Data Source:
- Primary source: DANE (Departamento Administrativo Nacional de Estadística)
- Update annually when official inflation data is published
- Can be entered manually through Django Admin

### Future Enhancements (Not in Current Scope):
- Payment tracking (handled by third-party provider)
- Email notifications to clients
- Client portal for viewing billing history
- Automatic CPI data fetching from DANE API
- Multi-currency support
- Contract renewal workflows

---

## 🚀 Getting Started

### Prerequisites:
- [ ] Django environment is running
- [ ] Database access configured
- [ ] Admin user exists for Django Admin

### Start with Phase 1:
1. Review the Cliente model specification
2. Switch to agent mode in Cursor
3. Request Phase 1 implementation
4. Test thoroughly before moving to Phase 2

---

## 📞 Questions Before Implementation?

Before starting Phase 1, ensure:
1. Client data structure is confirmed
2. Colombian phone format is acceptable (10 digits, no +57)
3. Unique constraints are appropriate
4. All required fields are identified

---

*Document Version: 1.0*  
*Last Updated: October 27, 2025*  
*Status: Ready for Phase 1 Implementation*

