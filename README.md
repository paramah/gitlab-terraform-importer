# GitLab Terraform Importer - Clean Architecture Edition

Zaawansowane narzędzie do importowania struktury grup i projektów GitLab do konfiguracji Terraform, zbudowane w oparciu o Clean Architecture. Umożliwia analizę niestandardowych modułów Terraform, parsowanie planów i automatyczne generowanie importów.

## 🎯 Funkcje

- 🏗️ **Clean Architecture** - Oddzielenie warstw: Domain, Application, Infrastructure, Interface
- 🔄 **Import struktury GitLab** - Rekurencyjne importowanie hierarchii grup i projektów
- 🌐 **Dual API Support** - Wykorzystanie REST API i GraphQL GitLab SDK
- 📦 **Analiza modułów Terraform** - Parsowanie i walidacja niestandardowych modułów
- 📋 **Terraform Plan Parser** - Analiza planów Terraform (JSON format)
- 🔍 **Module Variable Analyzer** - Szczegółowa analiza zmiennych w modułach
- 🚀 **Auto-import Generator** - Automatyczne generowanie skryptów `terraform import`
- ⚙️ **ENV Configuration** - Pełna konfiguracja przez zmienne środowiskowe
- 🎨 **Rich CLI** - Kolorowy interfejs z progress barami i tree view

## 📐 Architektura

Projekt wykorzystuje Clean Architecture z wyraźnym podziałem na warstwy:

```
src/gitlab_terraform_importer/
├── domain/                    # Warstwa domenowa (encje, interfejsy)
│   ├── entities/             # Group, Project, TerraformResource, etc.
│   └── repositories/         # Abstrakcje repozytoriów
├── application/              # Warstwa aplikacji (logika biznesowa)
│   └── use_cases/           # Use cases (Import, Analyze, Generate)
├── infrastructure/           # Warstwa infrastruktury (implementacje)
│   ├── gitlab/              # GitLab client (REST + GraphQL)
│   └── terraform/           # Terraform parser, analyzer, generator
└── interfaces/              # Warstwa interfejsów
    └── cli/                # Click-based CLI
```

### Główne komponenty:

#### Domain Layer
- **Entities** (Pydantic BaseModel): `Group`, `Project`, `TerraformResource`, `TerraformModule`, `TerraformPlan`, `TerraformState`
  - Automatyczna walidacja danych
  - JSON serialization/deserialization
  - Computed fields (@computed_field)
  - Field validators
- **Repository Interfaces**: `GitLabRepository`, `TerraformRepository`

#### Application Layer
- **ImportGitLabStructureUseCase** - Import struktury z GitLab
- **AnalyzeTerraformModulesUseCase** - Analiza modułów Terraform
- **GenerateTerraformImportsUseCase** - Generowanie konfiguracji import

#### Infrastructure Layer
- **GitLabClient** - Implementacja GitLab API (REST + GraphQL)
- **TerraformClient** - Parser, analyzer i generator Terraform

## 🚀 Wymagania

- Python 3.13+
- GitLab Personal Access Token z uprawnieniami `api`
- Terraform 1.0+ (opcjonalnie, do użycia wygenerowanych plików)

## 📦 Instalacja

```bash
# Klonowanie repozytorium
git clone <repository-url>
cd gitlab-terraform-importer

# Instalacja
pip install -e .

# Lub z poetry
poetry install
```

### Zależności

- `python-gitlab` - GitLab REST API
- `gql` - GitLab GraphQL API
- `python-hcl2` - Parsowanie plików Terraform (.tf)
- `python-terraform` - Interakcja z Terraform
- `pydantic` & `pydantic-settings` - Konfiguracja i walidacja
- `click` - CLI framework
- `rich` - Kolorowy output

## ⚙️ Konfiguracja

### 1. Utwórz plik `.env`

```bash
cp .env.example .env
```

### 2. Wypełnij zmienne środowiskowe

```bash
# Wymagane
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-personal-access-token

# Wymagane (jedno z poniższych)
GITLAB_ROOT_GROUP_ID=12345
# LUB
GITLAB_ROOT_GROUP_PATH=my-organization

# Opcjonalne
GITLAB_OUTPUT_DIR=./terraform
GITLAB_INCLUDE_ARCHIVED=false
GITLAB_MAX_DEPTH=5
GITLAB_TIMEOUT=60
GITLAB_VERIFY_SSL=true
```

## 📖 Użycie

### Walidacja konfiguracji

```bash
gitlab-tf-import validate-config
```

### Inspekcja struktury GitLab

```bash
# Widok drzewa (z rich formatting)
gitlab-tf-import inspect

# Format JSON
gitlab-tf-import inspect --format json
```

### Import i generowanie Terraform (podstawowe)

```bash
# Podstawowy import
gitlab-tf-import import-structure

# Z niestandardowym katalogiem
gitlab-tf-import import-structure --output-dir ./my-terraform

# Dry run
gitlab-tf-import import-structure --dry-run

# Verbose mode
gitlab-tf-import -v import-structure
```

### Analiza modułów Terraform

Nowa funkcjonalność! Analizuj niestandardowe moduły Terraform:

```bash
gitlab-tf-import analyze-modules \
  ./modules/gitlab-group \
  ./modules/gitlab-project
```

Output:
```
Module Analysis:

Group Module:
  Name:              gitlab-group
  Path:              ./modules/gitlab-group
  Variables:         8
  Required:          3
  Resources:         1
  Compatible:        ✓

Project Module:
  Name:              gitlab-project
  Path:              ./modules/gitlab-project
  Variables:         15
  Required:          5
  Resources:         1
  Compatible:        ✓
```

### Import z niestandardowymi modułami

Najważniejsza funkcjonalność! Import GitLab z wykorzystaniem Twoich modułów:

```bash
gitlab-tf-import import-with-modules \
  ./modules/gitlab-group \
  ./modules/gitlab-project \
  --output-dir ./terraform
```

Ten komenda:
1. Analizuje moduły Terraform (zmienne, outputs, resources)
2. Importuje strukturę GitLab
3. Mapuje dane GitLab do definicji w modułach
4. Generuje pliki `.tf` kompatybilne z modułami
5. Tworzy skrypt importu `import.sh`

## 🔧 Zaawansowane użycie

### Parsowanie Terraform Plan

```python
from gitlab_terraform_importer import TerraformClient
from pathlib import Path

client = TerraformClient()

# Parsowanie planu
plan = client.parse_plan(Path("terraform-plan.json"))

# Analiza zmian
resources_to_create = plan.get_resources_to_create()
resources_to_import = plan.get_resources_to_import()

print(f"Resources to create: {len(resources_to_create)}")
print(f"Resources to import: {len(resources_to_import)}")
```

### Praca z Pydantic Models

Wszystkie encje domenowe używają Pydantic BaseModel, co zapewnia:

```python
from gitlab_terraform_importer import Group, Project, TerraformModule

# Tworzenie z walidacją
group = Group(
    id=123,
    name="My Group",
    path="my-group",
    full_path="org/my-group",
    visibility="private"
)

# Automatyczna walidacja
# group = Group(id="invalid")  # Błąd: id musi być int

# JSON serialization
group_json = group.model_dump_json()
group_dict = group.model_dump()

# Deserialization
group_from_dict = Group.model_validate(group_dict)

# Computed fields
print(group.terraform_resource_name)  # "org_my_group"

# Summary bez nested obiektów
summary = group.model_dump_summary()
```

### Programatyczne użycie

```python
from gitlab_terraform_importer import (
    load_config,
    GitLabClient,
    TerraformClient,
    ImportGitLabStructureUseCase,
    GenerateTerraformImportsUseCase,
)
from pathlib import Path

# Konfiguracja
config = load_config()

# Klienci
gitlab_client = GitLabClient(config)
terraform_client = TerraformClient()

# Use cases
import_uc = ImportGitLabStructureUseCase(gitlab_client)
generate_uc = GenerateTerraformImportsUseCase(terraform_client)

# Import
root_group = import_uc.execute(
    root_group_path="my-organization",
    max_depth=3
)

# Parsowanie modułów
group_module = terraform_client.parse_module(Path("./modules/gitlab-group"))
project_module = terraform_client.parse_module(Path("./modules/gitlab-project"))

# Generowanie
result = generate_uc.execute(
    gitlab_structure=root_group,
    group_module=group_module,
    project_module=project_module,
    output_dir=Path("./terraform")
)

print(f"Generated {result['resources_count']} resources")
```

## 📁 Struktura wygenerowanych plików

```
terraform/
├── provider.tf          # Konfiguracja providera GitLab
├── groups.tf           # Definicje wszystkich grup
├── projects.tf         # Definicje wszystkich projektów
└── import.sh           # Skrypt importu (executable)
```

## 🎨 Przykładowy output CLI

```
✓ Configuration is valid!

Settings:
  GitLab URL:        https://gitlab.com
  Token:             ******** (set)
  Root Group Path:   my-organization
  Output Dir:        ./terraform

⠹ Importing GitLab structure...

Discovered:
  Groups:   15
  Projects: 47

⠹ Generating Terraform files...

✓ Success! Terraform files generated.

Generated:
  Resources:     62
  Files:         3
  Import Script: ./terraform/import.sh

Next steps:
  1. cd ./terraform
  2. terraform init
  3. Review generated files
  4. Run ./import.sh to import resources
  5. terraform plan
```

## 🧪 Use Cases

### Use Case 1: Migracja istniejącej infrastruktury

```bash
# 1. Sprawdź konfigurację
gitlab-tf-import validate-config

# 2. Przejrzyj strukturę
gitlab-tf-import inspect

# 3. Wygeneruj Terraform
gitlab-tf-import import-structure

# 4. Zaimportuj do state
cd terraform
terraform init
./import.sh

# 5. Weryfikuj
terraform plan  # Powinno być "no changes"
```

### Use Case 2: Praca z niestandardowymi modułami

```bash
# 1. Przeanalizuj moduły
gitlab-tf-import analyze-modules ./modules/group ./modules/project

# 2. Import z modułami
gitlab-tf-import import-with-modules \
  ./modules/group \
  ./modules/project

# 3. Dostosuj wygenerowane pliki do modułów
# 4. terraform import
```

### Use Case 3: Audit struktury GitLab

```bash
# Eksport do JSON dla dalszej analizy
gitlab-tf-import inspect --format json > gitlab-structure.json

# Analiza w jq
cat gitlab-structure.json | jq '.subgroups | length'
cat gitlab-structure.json | jq '.. | .projects? | select(. != null) | length'
```

## 🔍 Terraform Module Requirements

Aby moduły były kompatybilne, powinny:

1. Zawierać resource typu `gitlab_group` lub `gitlab_project`
2. Definiować zmienne dla podstawowych atrybutów (name, path, visibility, etc.)
3. (Opcjonalnie) Eksportować outputs (id, full_path)

Przykład modułu:

```hcl
# modules/gitlab-group/main.tf
variable "name" {
  type        = string
  description = "Group name"
}

variable "path" {
  type = string
}

variable "visibility" {
  type    = string
  default = "private"
}

resource "gitlab_group" "this" {
  name             = var.name
  path             = var.path
  visibility_level = var.visibility
}

output "id" {
  value = gitlab_group.this.id
}
```

## 📊 Zmienne środowiskowe

| Zmienna | Opis | Wymagana | Domyślna |
|---------|------|----------|----------|
| `GITLAB_URL` | URL instancji GitLab | Nie | `https://gitlab.com` |
| `GITLAB_TOKEN` | Personal Access Token | **Tak** | - |
| `GITLAB_ROOT_GROUP_ID` | ID grupy głównej | Tak* | - |
| `GITLAB_ROOT_GROUP_PATH` | Ścieżka grupy głównej | Tak* | - |
| `GITLAB_OUTPUT_DIR` | Katalog wyjściowy | Nie | `./terraform` |
| `GITLAB_TIMEOUT` | Timeout API (s) | Nie | `60` |
| `GITLAB_VERIFY_SSL` | Weryfikacja SSL | Nie | `true` |
| `GITLAB_INCLUDE_ARCHIVED` | Uwzględnij archived | Nie | `false` |
| `GITLAB_MAX_DEPTH` | Maks. głębokość | Nie | `None` |

\* Wymagane jest podanie `GITLAB_ROOT_GROUP_ID` **lub** `GITLAB_ROOT_GROUP_PATH`

## 🏗️ Rozwój

### Struktura projektu

```
src/gitlab_terraform_importer/
├── domain/
│   ├── entities/
│   │   ├── group.py
│   │   ├── project.py
│   │   └── terraform_resource.py
│   └── repositories/
│       ├── gitlab_repository.py
│       └── terraform_repository.py
├── application/
│   └── use_cases/
│       ├── import_gitlab_structure.py
│       ├── analyze_terraform_modules.py
│       └── generate_terraform_imports.py
├── infrastructure/
│   ├── gitlab/
│   │   └── gitlab_client.py
│   └── terraform/
│       ├── terraform_parser.py
│       ├── module_analyzer.py
│       ├── import_generator.py
│       └── terraform_client.py
└── interfaces/
    └── cli/
        └── commands.py
```

### Dodawanie nowych funkcji

1. **Nowa encja**: `domain/entities/`
2. **Nowy use case**: `application/use_cases/`
3. **Nowa implementacja**: `infrastructure/`
4. **Nowy komend CLI**: `interfaces/cli/commands.py`

## 🐛 Rozwiązywanie problemów

### Import timeout

```bash
GITLAB_TIMEOUT=120 gitlab-tf-import import-structure
```

### SSL Certificate Errors

```bash
GITLAB_VERIFY_SSL=false gitlab-tf-import import-structure
```

### Module parsing errors

Upewnij się, że moduły używają HCL2 syntax i są poprawnie sformatowane:

```bash
terraform fmt -recursive ./modules
```

## 📝 TODO / Roadmap

- [ ] Obsługa Terraform State do porównań
- [ ] Import members i permissions grup
- [ ] Wsparcie dla CI/CD variables
- [ ] Export do innych formatów (Pulumi, CDK)
- [ ] Web UI dla wizualizacji
- [ ] Diff między GitLab a Terraform state

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 Licencja

[Określ licencję]

## 👤 Autor

Aleksander Cynarski <aleksander@cynarski.pl>

## 🙏 Acknowledgments

- GitLab SDK Team
- Terraform Provider GitLab Team
- Clean Architecture by Robert C. Martin
