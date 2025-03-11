# 🍽️ Menza Lovec 

- Tento skript umožňuje vybrat a automaticky objednávat jídla ze stránek menzy TU Liberec.
- Skript kontroluje, zda je jídlo dostupné, a může jej zakoupit, jakmile se objeví v burze.
  
## 🔑 Získání autentifikačních tokenů

1. Otevřete prohlížeč Chrome a přejděte na adresu [https://menza.tul.cz/](https://menza.tul.cz/).

2. Stiskněte klávesu `F12` pro otevření vývojářských nástrojů.

3. Přejděte na záložku "**Application**" v horní liště.

4. V levém postranním panelu vyberte položku "**🍪 Cookies**". 

5. Najděte cookies s názvy a zkopírujte jejich hodnoty:
    - `MENZA-K8`
    - `_shibsession_`

6. Vložte zkopírované hodnoty do příslušných proměnných na začátku skriptu:
    - `MENZA_K8_TOKEN` pro hodnotu cookie `"MENZA-K8"`
    - `SHIBSESSION_TOKEN` pro hodnotu cookie `"_shibsession_"`

## 🚀 Spuštění

### **Windows** 🟥🟩🟦🟨
- Otevři si PowerShell a přejdi do složky, kde to chceš spustit.

| Krok | Příkaz |
| ---- | ------ |
| Vytvoření virtuálního prostředí | `python -m venv venv` |
| Aktivace virtuálního prostředí | `.\venv\Scripts\activate` |
| Instalace závislostí | `pip install -r requirements.txt` |
| Spuštění skriptu | `python main.py` |

### **Linux & macOS** 🐧🍎
| Krok | Příkaz |
| ---- | ------ |
| Vytvoření virtuálního prostředí | `python3 -m venv venv` |
| Aktivace virtuálního prostředí | `source venv/bin/activate` |
| Instalace závislostí | `pip install -r requirements.txt` |
| Spuštění skriptu | `python3 main.py` |




## Bezpečnost a soukromí
- Tento skript používá tokeny pouze pro získání dostupných jídel a objednání jídla
- Vaše tokeny jsou uloženy pouze lokálně a nejsou nikam odesílány, kromě oficiálního webu menza.tul.cz
