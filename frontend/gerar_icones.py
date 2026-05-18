# Cria ícones simples em SVG convertidos para PNG via base64
import base64, os

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#1A1208"/>
  <text x="256" y="200" font-size="180" text-anchor="middle" fill="#C9A84C" font-family="serif">✦</text>
  <text x="256" y="360" font-size="72" text-anchor="middle" fill="#FAF6EE" font-family="serif" font-style="italic">Manhã</text>
  <text x="256" y="440" font-size="52" text-anchor="middle" fill="#C9A84C" font-family="serif" font-style="italic">com Deus</text>
</svg>'''

with open("icon.svg", "w") as f:
    f.write(svg)

print("SVG criado! Use https://svgtopng.com para converter em 192x192 e 512x512")
print("Salve como icon-192.png e icon-512.png na pasta frontend/")
