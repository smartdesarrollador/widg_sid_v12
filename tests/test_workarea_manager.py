"""
Script de testing para WorkareaManager
Permite probar la reserva de espacio en Windows
"""

import sys
from pathlib import Path
import time

# Agregar src al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / 'src'))

from core.workarea_manager import WorkareaManager


def test_workarea_basic():
    """Test básico de reserva y restauración de espacio"""
    print("\n" + "="*60)
    print("WORKAREA MANAGER - BASIC TEST")
    print("="*60)

    manager = WorkareaManager()

    # Mostrar estado original
    status = manager.get_status()
    print(f"\nEstado inicial:")
    print(f"  Reservado: {status['is_reserved']}")
    print(f"  Ancho: {status['width']}px")
    print(f"  Lado: {status['side']}")
    print(f"  Original: {status['original']}")

    print("\n[TEST 1] Reservando 540px en el lado derecho...")
    success = manager.reserve_space_right(540)

    if success:
        print("  ✓ Espacio reservado exitosamente")
        print("  → Abre alguna ventana y observa que se ajusta al espacio disponible")
    else:
        print("  ✗ Error al reservar espacio")

    # Mostrar estado después de reservar
    status = manager.get_status()
    print(f"\nEstado después de reservar:")
    print(f"  Reservado: {status['is_reserved']}")
    print(f"  Ancho: {status['width']}px")
    print(f"  Lado: {status['side']}")

    # Esperar para que el usuario vea el cambio
    print("\nEsperando 5 segundos para que veas el efecto...")
    time.sleep(5)

    print("\n[TEST 2] Restaurando área de trabajo original...")
    success = manager.restore_workarea()

    if success:
        print("  ✓ Área restaurada exitosamente")
        print("  → Las ventanas deberían volver a ocupar toda la pantalla")
    else:
        print("  ✗ Error al restaurar área")

    # Mostrar estado final
    status = manager.get_status()
    print(f"\nEstado final:")
    print(f"  Reservado: {status['is_reserved']}")
    print(f"  Ancho: {status['width']}px")
    print(f"  Lado: {status['side']}")

    print("\n" + "="*60)
    print("TEST COMPLETADO")
    print("="*60)


def test_workarea_left():
    """Test de reserva en el lado izquierdo"""
    print("\n" + "="*60)
    print("WORKAREA MANAGER - LEFT SIDE TEST")
    print("="*60)

    manager = WorkareaManager()

    print("\nReservando 540px en el lado IZQUIERDO...")
    success = manager.reserve_space_left(540)

    if success:
        print("  ✓ Espacio reservado exitosamente en el lado izquierdo")
        print("  → Abre alguna ventana y observa que se ajusta")
    else:
        print("  ✗ Error al reservar espacio")

    print("\nEsperando 5 segundos...")
    time.sleep(5)

    print("\nRestaurando área de trabajo...")
    manager.restore_workarea()

    print("\nTEST COMPLETADO")


def test_workarea_multiple():
    """Test de múltiples reservas"""
    print("\n" + "="*60)
    print("WORKAREA MANAGER - MULTIPLE RESERVATIONS TEST")
    print("="*60)

    manager = WorkareaManager()

    print("\n[1] Reservando 300px en el lado derecho...")
    manager.reserve_space_right(300)
    time.sleep(2)

    print("[2] Reservando 500px en el lado derecho (debería sobrescribir)...")
    manager.reserve_space_right(500)
    time.sleep(2)

    print("[3] Reservando 400px en el lado izquierdo (debería cambiar de lado)...")
    manager.reserve_space_left(400)
    time.sleep(2)

    print("[4] Restaurando...")
    manager.restore_workarea()

    print("\nTEST COMPLETADO")


def test_workarea_integration():
    """Test de integración con controller"""
    print("\n" + "="*60)
    print("WORKAREA MANAGER - INTEGRATION TEST")
    print("="*60)

    from controllers.main_controller import MainController

    print("\nCreando MainController...")
    controller = MainController()

    print(f"WorkareaManager disponible: {hasattr(controller, 'workarea_manager')}")

    if hasattr(controller, 'workarea_manager'):
        manager = controller.workarea_manager

        print("\nReservando espacio a través del controller...")
        success = manager.reserve_space_right(540)

        if success:
            print("  ✓ Espacio reservado exitosamente")
        else:
            print("  ✗ Error al reservar espacio")

        time.sleep(3)

        print("\nRestaurando...")
        manager.restore_workarea()

    print("\nTEST COMPLETADO")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test WorkareaManager')
    parser.add_argument(
        '--mode',
        choices=['basic', 'left', 'multiple', 'integration'],
        default='basic',
        help='Modo de testing (default: basic)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("IMPORTANTE: Este test modificará temporalmente el área de trabajo")
    print("de Windows. Las ventanas abiertas se ajustarán automáticamente.")
    print("="*60)

    input("\nPresiona ENTER para continuar...")

    if args.mode == 'basic':
        test_workarea_basic()
    elif args.mode == 'left':
        test_workarea_left()
    elif args.mode == 'multiple':
        test_workarea_multiple()
    elif args.mode == 'integration':
        test_workarea_integration()
