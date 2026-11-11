"""Desde la raíz: python scripts/verificar_resultados.py. No optimiza."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from setcover.cli import main
if __name__=='__main__':
    sys.argv=[sys.argv[0],'verificar']
    main()