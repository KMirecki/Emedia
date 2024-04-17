class Chunk:
    def __init__(self, length, name, data, checksum):
        self.length = length
        self.name = name
        self.data = data
        self.checksum = checksum
    
    def printInfo(self):
        return "\nDługość chunku:\t" + str(self.length) + "\nNazwa chunku:\t" + str(self.name)
        #+ "\nSuma kontrolna CRC32:\t" + str(self.checksum)

    def decode_cHRM_chunk(self):
        print("Informacje zawarte w chunku cHRM")
        whitePointX = bytes_to_int(self.data[0:4])/100000
        whitePointY = bytes_to_int(self.data[4:8])/100000
        redX = bytes_to_int(self.data[8:12])/100000
        redY = bytes_to_int(self.data[12:16])/100000
        greenX = bytes_to_int(self.data[16:20])/100000
        greenY = bytes_to_int(self.data[20:24])/100000
        blueX = bytes_to_int(self.data[24:28])/100000
        blueY = bytes_to_int(self.data[28:32])/100000
        print("White Point X: ", whitePointX,
              "\nWhite Point Y: ", whitePointY,
              "\nredX: ", redX,
              "\nredY: ", redY,
              "\ngreenX: ", greenX,
              "\ngreenY: ", greenY,
              "\nblueX: ", blueX,
              "\nblueY: ", blueY)

    def decode_IHDR_chunk(self):
        #print(self.data)
        print("Informacje zawarte w chunku IHDR")
        width = bytes_to_int(self.data[0:4])
        height = bytes_to_int(self.data[4:8])
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
        
        #niepotwierdzone
        match self.data[10]:
            case 0:
                compression_method = "Brak kompresji"
            case 1:
                compression_method = "Kompresja LZ77 z kodowaniem kanalow filtracji"
            case 2:
                compression_method = "Kompresja LZ77 z kodowaniem kanalow filtracji i strategia kompresji danych"

        match self.data[11]:
            case 0:
                filter_method = "None"
            case 1:
                filter_method = "Sub"
            case 2:
                filter_method = "Up"
            case 3:
                filter_method = "Average"
            case 4:
                filter_method = "Paeth"
        
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

    def decode_gAMA_chunk(self):
        print("Informacje zawarte w chunku gAMA")
        chunk_gamma = bytes_to_int(self.data)/100000
        print("Wartość gamma odczytana z chunku: ", chunk_gamma)
        real_gamma = round((1/chunk_gamma),3)
        print("Faktyczna wartość gamma: ", real_gamma)

    def decode_tEXt_chunk(self):
        print("Informacje zawarte w chunku tEXT")
        text=""
        for byte in self.data:
            text+=chr(byte)
        print(text)
    
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
    
    def decode_IEND_chunk(self):
        print(self.length)
        print(self.name)
        #do obliczenia checksuma
        print(self.checksum)


def save_decimal_data(png_file):
    decimal_data = []
    with open(png_file, 'rb') as f:
        binary_data = f.read()

        for byte in binary_data:
            decimal_data.append(byte)

    png_check = decimal_data[0:8]
    if png_check == [137, 80, 78, 71, 13, 10, 26, 10]:
        # print("It's a PNG.")
        return decimal_data
    else:
        # print("File is not a PNG.")
        raise ValueError("File is not a PNG")

def chunk_name(chunk):
    chunk_name=''
    for byte in chunk:
        chunk_name += chr(byte)
    return chunk_name

def chunk_length(chunk):
    chunk_length = 12+bytes_to_int(chunk)
    return chunk_length

def bytes_to_int(chunk):
    new_chunk = chunk[0]*pow(256,3)+chunk[1]*pow(256,2)+chunk[2]*256+chunk[3]
    return new_chunk

#do poprawienia
#def chunk_checksum(chunk):
#    chunk_checksum = 12+chunk[0]*pow(256,3)+chunk[1]*pow(256,2)+chunk[2]*256+chunk[3]
#    return chunk_checksum

def chunk_decoder(chunk, chunks_list):
    if(len(chunk)>=12):
        #chunk_info = ""
        length = chunk_length(chunk[0:4])
        #data_length=length-12
        name = chunk_name(chunk[4:8])
        data = chunk[8:length-4]
        checksum = chunk[length-4:length]
        new_chunk = Chunk(length,name,data,checksum)
        chunks_list.append(new_chunk)
        #chunk_info+="dlugosc chunku "+str(length)+" nazwa chunku "+str(name)
        remaining_chunk=chunk[length:]
        chunk_decoder(remaining_chunk, chunks_list)
    return chunks_list

if __name__ == "__main__":
    png_file = 'PNG_transparency_demonstration_1.png'
    dec_data = save_decimal_data(png_file)
    if(dec_data[:8]==[137, 80, 78, 71, 13, 10, 26, 10]):
        print("Wartosc pierwszych 8 bajtow pliku:\n", dec_data[0:8])  
        #chunk_decoder(dec_data[8:])
        chunks_list=[]
        chunks_list = chunk_decoder(dec_data[8:],chunks_list)
        for chunk in chunks_list:
            print(chunk.printInfo())
            match chunk.name:
                case "IHDR":
                    chunk.decode_IHDR_chunk()
                case "cHRM":
                    chunk.decode_cHRM_chunk()
                case "gAMA":
                    chunk.decode_gAMA_chunk()
                case "bKGD":
                    chunk.decode_bKGD_chunk()
                case "tIME":
                    chunk.decode_tIME_chunk()
                case "tEXt":
                    chunk.decode_tEXt_chunk()
                case "IEND":
                    chunk.decode_IEND_chunk()
    else:
        raise TypeError("File is not a png")