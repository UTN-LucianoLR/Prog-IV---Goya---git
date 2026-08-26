productos = [
    {"nombre": "Laptop", "precio": 1200, "stock": 15},
    {"nombre": "Mouse", "precio": 25, "stock": 5},
    {"nombre": "Teclado", "precio": 75, "stock": 25},
    {"nombre": "Monitor", "precio": 200, "stock": 8},
]

# print (productos[1]["nombre"]) 
# print (productos[2]["precio"])


# # Crea una lista vacía llamada donde se van a guardar posteriormente los productos cuyo stock sea menor a 10 unidades.
# productos_bajo_stock = []

# # Recorre uno por uno todos los elementos que están dentro de la lista "productos".
# # En cada iteración del for, la variable "producto" representa un producto diferente de la lista.
# for producto in productos:

#     # Muestra por pantalla el nombre y el precio del producto actual.
#     # La letra "f" antes del texto permite utilizar una f-string,
#     # que permite insertar valores de variables o expresiones dentro de {}.
#     print(f"Producto: {producto['nombre']}, Precio: ${producto['precio']}")

#     # Comprueba si el stock del producto actual es menor que 10.
#     # "¿El producto actual tiene menos de 10 unidades disponibles?"
#     if producto['stock'] < 10:

#         # Si la condición anterior es verdadera, agrega el producto actual
#         # completo a la lista "productos_bajo_stock".
#         #
#         # append() es un método de listas que agrega un elemento al final de la lista.
#         productos_bajo_stock.append(producto)

# # Imprime un mensaje en la consola.
# print("\nProductos con bajo stock:")

# # Muestra por pantalla el contenido completo de la lista "productos_bajo_stock".
# # Como se agregaron los diccionarios completos mediante append(), se muestra cada producto con todas sus claves y valores.
# print(productos_bajo_stock)

# # Define con "def" (palabra reservada de Python) la función llamada "calcular_promedio_precio".
# # "(lista)" indica que la función recibe un parámetro llamado "lista".
# # Dicho parámetro representa la lista de productos sobre la cual se va a calcular el promedio.
# def calcular_promedio_precio(lista):

#     # Comprueba si la lista está vacía, haciendo uso del "not".
#     # evitando intentar calcular un promedio cuando no hay productos.
#     if not lista:

#         # "return" termina la ejecución de la función y devuelve un valor
#         # si la lista está vacía, la función devuelve 0.
#         return 0


#     # Calcula la suma de los precios de todos los productos de la lista
#     # y guarda el resultado en la variable "total_precio".
    
#     # "sum()" es una FUNCIÓN INCORPORADA (built-in) de Python que recibe
#     # una colección de valores numéricos y devuelve la SUMA de todos ellos.
#     total_precio = sum(p['precio'] for p in lista)


#     # Calcula y devuelve el precio promedio.
#     # "len()" es una FUNCIÓN INCORPORADA de Python que devuelve la
#     # CANTIDAD DE ELEMENTOS que contiene una colección.
#     return total_precio / len(lista)

# # Llama (ejecuta) a la función "calcular_promedio_precio".
# precio_promedio = calcular_promedio_precio(productos)

# # Muestra el resultado por pantalla.
# # La "f" antes de las comillas indica que estamos utilizando una F-STRING (formatted string).
# # Una f-string permite insertar variables o expresiones dentro de un texto utilizando llaves {}.

# # ":.2f" indica cómo queremos FORMATEAR ese número:
# #     ":"       → comienza la especificación de formato.
# #     ".2"      → queremos mostrar 2 cifras después del punto decimal.
# #     "f"       → queremos mostrar el número en formato de punto flotante.
# print(f"\nEl precio promedio de los productos es: ${precio_promedio:.2f}")

import csv

productos_desde_csv = []

with open('datos.csv', mode='r', encoding='utf-8') as archivo_csv:
    lector_diccionario = csv.DictReader(archivo_csv)
    for fila in lector_diccionario:
        fila["id"] = int(fila["id"]) 
        fila['precio'] = int(fila['precio']) 
        fila['stock'] = int(fila['stock'])     
        productos_desde_csv.append(fila)

print("\nLista de productos desde el archivo CSV:")
print(productos_desde_csv)

print("\nLista de productos desde el archivo ordenado de CSV:")
for producto in productos_desde_csv:
    print(
        f"ID: {producto['id']} "
        f"Producto: {producto['nombre']} "
        f"Precio: ${producto['precio']} "
        f"Stock: {producto['stock']}"
    )