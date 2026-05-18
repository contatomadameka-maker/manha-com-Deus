from PIL import Image, ImageDraw
import math

def criar_icone(size):
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Fundo arredondado escuro
    r = int(size * 0.18)
    draw.rounded_rectangle([0,0,size,size], radius=r, fill=(26,18,8,255))
    
    # Gradiente sutil no topo
    for i in range(size//2):
        alpha = int(15 * (1 - i/(size//2)))
        draw.line([(0,i),(size,i)], fill=(44,31,14,alpha))
    
    # Cruz dourada centralizada (símbolo cristão limpo)
    cx, cy = size//2, int(size*0.42)
    cw = int(size*0.06)  # espessura
    ch = int(size*0.38)  # altura total da cruz
    cw2 = int(size*0.24) # largura do braço horizontal
    ch2 = int(size*0.06) # espessura horizontal
    cy_h = cy - int(size*0.04) # posição do braço horizontal
    
    gold = (201,168,76,255)
    gold_dark = (168,135,58,255)
    
    # Sombra suave da cruz
    draw.rectangle([cx-cw//2+2, cy-ch//2+2, cx+cw//2+2, cy+ch//2+2], fill=(0,0,0,60))
    draw.rectangle([cx-cw2//2+2, cy_h-ch2//2+2, cx+cw2//2+2, cy_h+ch2//2+2], fill=(0,0,0,60))
    
    # Cruz vertical
    draw.rectangle([cx-cw//2, cy-ch//2, cx+cw//2, cy+ch//2], fill=gold)
    # Cruz horizontal  
    draw.rectangle([cx-cw2//2, cy_h-ch2//2, cx+cw2//2, cy_h+ch2//2], fill=gold)
    
    # Brilho no centro da cruz
    highlight_size = int(size*0.04)
    draw.ellipse([cx-highlight_size, cy_h-highlight_size, cx+highlight_size, cy_h+highlight_size], 
                 fill=(232,201,126,180))
    
    # Linha decorativa dourada fina acima do texto
    line_y = int(size*0.72)
    line_w = int(size*0.35)
    draw.rectangle([cx-line_w//2, line_y, cx+line_w//2, line_y+int(size*0.008)], fill=(201,168,76,120))
    
    # Texto "Manhã" - usando pixels manualmente para garantir qualidade
    # Vamos usar PIL com fonte padrão escalada
    try:
        from PIL import ImageFont
        # Tenta fontes do sistema
        fontes = [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", 
            "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        ]
        font1 = None
        font2 = None
        for f in fontes:
            try:
                font1 = ImageFont.truetype(f, int(size*0.115))
                font2 = ImageFont.truetype(f, int(size*0.082))
                break
            except: pass
        
        if font1:
            # "Manhã" em creme
            draw.text((cx, int(size*0.775)), "Manhã", 
                     fill=(250,246,238,255), font=font1, anchor="mm")
            # "com Deus" em dourado
            draw.text((cx, int(size*0.882)), "com Deus", 
                     fill=(201,168,76,255), font=font2, anchor="mm")
        else:
            raise Exception("sem fonte")
    except:
        # Fallback sem fonte — só a cruz fica (ainda bonito)
        pass
    
    return img

for size in [192, 512]:
    img = criar_icone(size)
    img.save(f"frontend/icon-{size}.png", "PNG")
    print(f"✓ icon-{size}.png ({size}x{size})")

print("✓ Ícones criados!")
