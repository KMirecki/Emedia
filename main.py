import json
from PIL import Image
import io
import matplotlib.pyplot as plt
import cv2
import numpy as np

class Chunk:
    def __init__(self, length, name, length_translated, name_translated, data, checksum):
        self.length_translated = length_translated
        self.name_translated = name_translated
        self.length = length
        self.name = name
        self.data = data
        self.checksum = checksum
    
    def printInfo(self):
        return "\nDługość chunku:\t" + str(self.length_translated) + "\nNazwa chunku:\t" + str(self.name_translated)
    
    def printBytes(self):
        bytes_list = []
        bytes_list.extend(self.length)
        bytes_list.extend(self.name)
        bytes_list.extend(self.data)
        bytes_list.extend(self.checksum)
        return bytes_list

    def decode_cHRM_chunk(self):
        print("Informacje zawarte w chunku cHRM")
        whitePointX = int.from_bytes(self.data[0:4])/100000
        whitePointY = int.from_bytes(self.data[4:8])/100000
        redX = int.from_bytes(self.data[8:12])/100000
        redY = int.from_bytes(self.data[12:16])/100000
        greenX = int.from_bytes(self.data[16:20])/100000
        greenY = int.from_bytes(self.data[20:24])/100000
        blueX = int.from_bytes(self.data[24:28])/100000
        blueY = int.from_bytes(self.data[28:32])/100000
        print("White Point X: ", whitePointX,
              "\nWhite Point Y: ", whitePointY,
              "\nredX: ", redX,
              "\nredY: ", redY,
              "\ngreenX: ", greenX,
              "\ngreenY: ", greenY,
              "\nblueX: ", blueX,
              "\nblueY: ", blueY)

    def decode_IHDR_chunk(self):
        print("Informacje zawarte w chunku IHDR")
        width = int.from_bytes(self.data[0:4])
        height = int.from_bytes(self.data[4:8])
        color_type = ""
        compression_method = ""
        filter_method = ""
        interlance_method = ""

        match self.data[9]:
            case 0:
                color_type = "Grayscale"
            case 2:
                color_type = "Truecolor"
            case 3:
                color_type = "Indexed"
            case 4:
                color_type = "Grayscale and alpha"
            case 6:
                color_type = "Truecolor and alpha"
        
        match self.data[10]:
            case 0:
                compression_method = "DEFLATE"
            case _:
                print("nieprawidłowa metoda kompresji")

        match self.data[11]:
            case 0:
                filter_method = "Adaptive"
            case _:
                print("nieprawidlowa metoda filtrowania")
        
        match self.data[12]:
            case 0:
                interlance_method = "no interlance"
            case 1:
                interlance_method = "Adam7 interlance"

        print ("Szerokosc obrazu: ", width, "px",
               "\nWysokosc obrazu: ", height,"px",
               "\nBit depth (głebia bitowa): ", self.data[8], "bit",
               "\nTyp koloru: ", color_type,
               "\nMetoda kompresji: ",compression_method,
               "\nMetoda filtrowania: ",filter_method,
               "\nInterlace method (sposob renderowania obrazu): ",interlance_method)

    def decode_PLTE_chunk(self):
        if(self.length_translated%3!=0):
            print("nieprawidlowy chunk PLTE")
        else:
            full_color_list = []
            i = 0
            while self.data:
                if(i>=self.length_translated-12):
                    break
                color_list = []
                red = self.data[i]
                green = self.data[i+1]
                blue = self.data[i+2]
                color_list.append(red)
                color_list.append(green)
                color_list.append(blue)
                full_color_list.append(color_list)
                print("iteration: ",int((i/3)+1)," rgb values: ",color_list)
                i+=3
                #print(i)
            #print("liczba wystapien: ", i/3)
            #print(full_color_list)
            palette = [(r / 255, g / 255, b / 255) for r, g, b in full_color_list]
            fig, ax = plt.subplots(1, 1, figsize=(16, 2))
            for i, color in enumerate(palette):
                ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color, edgecolor='black'))
            ax.set_xlim(0, len(palette))
            ax.set_ylim(0, 1)
            ax.axis('off')
            plt.show()

    def decode_gAMA_chunk(self):
        print("Informacje zawarte w chunku gAMA")
        chunk_gamma = int.from_bytes(self.data)/100000
        print("Wartość gamma odczytana z chunku: ", chunk_gamma)
        #real_gamma = round((1/chunk_gamma),3)
        #print("Faktyczna wartość gamma: ", real_gamma)

    def decode_tEXt_chunk(self):
        print("Informacje zawarte w chunku tEXT")
        keyword=""
        i = 0
        text=""
        for byte in self.data:
            if(byte==0):
                i+=1
                break
            else:
                keyword+=chr(byte)
                i+=1
        for byte in self.data[i:]:
            text+=chr(byte)
        print("Keyword: ", keyword, "\n", text)
        #print(self.data)
    
    def decode_oFFs_chunk(self):
        x_position = int.from_bytes(self.data[0:4])
        y_position = int.from_bytes(self.data[4:8])
        if(self.data[8]==0):
            unit = "pixel"
        elif(self.data[8]==1):
            unit = "micrometer"
        print("X position: ",x_position, unit,
              "\nY position: ",y_position, unit,
              "\nUnit: ",unit)

    def decode_bKGD_chunk(self):
        print("Informacje zawarte w chunku bKGD")
        match len(self.data):
            case 1:
                print("Palette index: ", int.from_bytes(self.data))
            case 2:
                print("Gray: ", int.from_bytes(self.data))
            case 6:
                print("Red: ", int.from_bytes(self.data[0:2]),
                      "\nGreen: ", int.from_bytes(self.data[2:4]),
                      "\nBlue: ", int.from_bytes(self.data[4:6]))    
    
    def decode_tIME_chunk(self):
        print("Informacje zawarte w chunku tIME")
        year = int.from_bytes(self.data[0:2], "big")
        day = str(self.data[2]).zfill(2) if len(str(self.data[2])) == 1 else str(self.data[2])
        print("Ostatnia modyfikacja pliku: ",
              self.data[3],"/",day,"/",year," ",
              self.data[4],":",self.data[5],":",self.data[6])
    
    def decode_sRGB_chunk(self):
        match int.from_bytes(self.data):
            case 0:
                print("Rendering intent: Perceptual")
            case 1:
                print("Rendering intent: Relative colometric")
            case 2:
                print("Rendering intent: Saturation")
            case 3:
                print("Rendering intent: Absolute colometric")    

    def decode_sBIT_chunk(self):
        match len(self.data):
            case 1:
                print("significant grayscale bits: ", self.data)
            case 2:
                print("significant grayscale bits: ",self.data[0],"\nsignificant alpha bits: ",self.data[1])
            case 3:
                print("significant red bits: ",self.data[0],"\nsignificant green bits: ",self.data[1],
                      "\nsignificant blue bits: ", self.data[2])
            case 4:
                print("significant red bits: ",self.data[0],"\nsignificant green bits: ",self.data[1],
                      "\nsignificant blue bits: ", self.data[2], "\nsignificant alpha bits: ",self.data[3])


    def decode_IEND_chunk(self):
        print("Zawartosc chunka IEND")

def save_decimal_data(png_file):
    decimal_data = []
    with open(png_file, 'rb') as f:
        binary_data = f.read()

        for byte in binary_data:
            decimal_data.append(byte)

    png_check = decimal_data[0:8]
    if png_check == [137, 80, 78, 71, 13, 10, 26, 10]:
        return decimal_data
    else:
        raise ValueError("File is not a PNG")

def chunk_name(chunk):
    chunk_name=''
    for byte in chunk:
        chunk_name += chr(byte)
    return chunk_name

def chunk_length(chunk):
    chunk_length = 12+int.from_bytes(chunk)
    return chunk_length

def chunk_decoder(chunk, chunks_list):
    if(len(chunk)>=12):
        length = chunk[0:4]
        length_translated = chunk_length(chunk[0:4])
        name = chunk[4:8]
        name_translated = chunk_name(chunk[4:8])
        data = chunk[8:length_translated-4]
        checksum = chunk[length_translated-4:length_translated]
        new_chunk = Chunk(length,name,length_translated,name_translated,data,checksum)
        chunks_list.append(new_chunk)
        remaining_chunk=chunk[length_translated:]
        chunk_decoder(remaining_chunk, chunks_list)
    return chunks_list

def data_anonymization(chunks_list, dec_data_anon):
    for chunk in chunks_list:
        if(chunk.name_translated=="IHDR" or chunk.name_translated=="PLTE" or chunk.name_translated=="IDAT" or chunk.name_translated=="IEND"):
            dec_data_anon.extend(chunk.length)
            dec_data_anon.extend(chunk.name)
            dec_data_anon.extend(chunk.data)
            dec_data_anon.extend(chunk.checksum)
    return dec_data_anon

if __name__ == "__main__":
    #png_file = 'pnglogo--povray-3.7--black826--800x600.png'
    #png_file = 'PNG_transparency_demonstration_1.png'
    #png_file = 'pobrane.png'
    #png_file = 'pobrane (1).png'
    png_file = 'Lenna_(test_image).png'
    #png_file = 'pobrane.jpg'
    #png_file = 'pp0n6a08.png'
    #png_file = 'anon.png'
    #png_file = '12-tree-png-image-download-picture-thumb.png'
    dec_data = save_decimal_data(png_file)
    png_file_signature = [137, 80, 78, 71, 13, 10, 26, 10]
    with open("png.txt", "w") as file:
        json.dump(dec_data, file)
    
    chunks_list=[]
    chunks_list_anon = []
    dec_data_anon = []
    dec_data_anon.extend(dec_data[0:8])
    if(dec_data[0:8]==png_file_signature):
        print("Pierwsze 8 bajtow pliku - sygnatura PNG:\n", dec_data[0:8])  
        #chunk_decoder(dec_data[8:])
        chunks_list = chunk_decoder(dec_data[8:],chunks_list)
        dec_data_anon = data_anonymization(chunks_list, dec_data_anon)
        chunks_list_anon = chunk_decoder(dec_data_anon[8:], chunks_list_anon)
        #print(len(dec_data))
        #print(len(dec_data_anon))
        #print("\n",chunks_list_anon)
        with open("png_anon.txt", "w") as file:
            json.dump(dec_data_anon, file)
        #for chunk in chunks_list_anon:
        for chunk in chunks_list:
            print(chunk.printInfo())
            match chunk.name_translated:
                case "IHDR":
                    chunk.decode_IHDR_chunk()
                    print(chunk.printBytes())
                case "PLTE":
                    chunk.decode_PLTE_chunk()
                    #print(chunk.printBytes())
                case "cHRM":
                    chunk.decode_cHRM_chunk()
                    print(chunk.printBytes())
                case "gAMA":
                    chunk.decode_gAMA_chunk()
                    print(chunk.printBytes())
                case "bKGD":
                    chunk.decode_bKGD_chunk()
                    print(chunk.printBytes())
                case "tIME":
                    chunk.decode_tIME_chunk()
                    print(chunk.printBytes())
                case "tEXt":
                    chunk.decode_tEXt_chunk()
                    print(chunk.printBytes())
                case "sBIT":
                    chunk.decode_sBIT_chunk()
                    print(chunk.printBytes())
                case "oFFs":
                    chunk.decode_oFFs_chunk()
                    print(chunk.printBytes())
                case "IEND":
                    chunk.decode_IEND_chunk()
                    print(chunk.printBytes())
                    break
                case "sRGB":
                    chunk.decode_sRGB_chunk()
                    print(chunk.printBytes())
                case "IDAT":
                    if(chunk.length_translated==0):
                        break
                case _:
                    print(chunk.printBytes())

        data_bytes = bytes(dec_data)
        data_bytes_anon = bytes(dec_data_anon)
        image = Image.open(io.BytesIO(data_bytes))
        image_anon = Image.open(io.BytesIO(data_bytes_anon))

        #fast fourier transform
        img = cv2.imread(png_file, cv2.IMREAD_GRAYSCALE)
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift))
        phase_spectrum = np.angle(fshift)

        #usunięcie niskich częstotliwości i zostawienie x procent najwyższych częstotliwości
        rows, cols = img.shape
        crow, ccol = rows // 2 , cols // 2
        mask = np.zeros((rows, cols), np.uint8)
        percent = 0.5
        size = int(percent * rows * cols)
        sorted_indices = np.unravel_index(np.argsort(np.abs(fshift).ravel())[::-1], fshift.shape)
        top_indices = (sorted_indices[0][:size], sorted_indices[1][:size])
        mask[top_indices] = 1
        fshift_filtered = fshift * mask

        #odtworzenie obrazu odwrotną transformatą fouriera
        magnitude_spectrum_filtered = 20 * np.log(np.abs(fshift_filtered))
        f_ishift = np.fft.ifftshift(fshift_filtered)
        img_ifft = np.fft.ifft2(f_ishift)
        img_ifft = np.abs(img_ifft)

        #różnica między oryginalnym obrazem a odtworzonym
        img_diff = np.abs(img - img_ifft)

        plt.figure()
        plt.subplot(1, 2, 1)
        plt.imshow(image)
        plt.title('Image')
        plt.axis('off')
        plt.subplot(1, 2, 2)
        plt.imshow(image_anon)
        plt.title('Anonymous Image')
        plt.axis('off')

        plt.figure()
        plt.subplot(2,3,1)
        plt.imshow(img, cmap='gray')
        plt.title('Image grayscale')
        plt.axis('off')
        plt.subplot(2,3,2)
        plt.imshow(magnitude_spectrum, cmap='gray')
        plt.title('magnitude')
        plt.axis('off')
        plt.subplot(2,3,3)
        plt.imshow(phase_spectrum, cmap='gray')
        plt.title('phase')
        plt.axis('off')
        plt.subplot(2,3,5)
        plt.imshow(img_ifft, cmap='gray')
        plt.title('restored image')
        plt.axis('off')
        plt.subplot(2,3,4)
        plt.imshow(magnitude_spectrum_filtered, cmap='gray')
        plt.title('magnitude '+str(percent*100)+'%')
        plt.axis('off')
        plt.subplot(2,3,6)
        plt.imshow(img_diff, cmap='gray')
        plt.title('difference')
        plt.axis('off')
        plt.show()

        #image = image.save("file.png")
        #image_anon = image_anon.save("anon.png")

    else:
        raise TypeError("File is not a png")