import os 
import time
import matplotlib.pyplot as plt
import itertools
import numpy
import ast
from itertools import groupby
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from music21 import *
from re import *
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

global n1txtbox, n2txtbox, compareButton, n1, n2, TVõ1, TVõ2, TVV, start_time, TVV2

#Avab failidialoogi ja valmistab ette noodi sisselugemiseks ning teostab kogu protsessi
#Kontrollib noodifailide avamise protsessi
def on_open():
    global note1, note2, n1, n2, start_time, frontLabelRdy, levButton
    file2write=open("log.txt",'a')
    file2write.close()
    if note1 !='' and note2 !='':
        result = messagebox.askokcancel("Diginootide meloodiaanalüsaator","Kaks noodistust on valitud. Kas soovid valida uued?")
        if result == True:
            note1 = ''
            note2 = ''
            n1 = ''
            n2 = ''
            TVV.config(state="normal")
            TVõ1.config(state="normal")
            TVõ2.config(state="normal")
            TVV.delete('1.0', END)
            TVõ1.delete('1.0', END)
            TVõ2.delete('1.0', END)
            TVV.config(state="disabled")
            TVõ1.config(state="disabled")
            TVõ2.config(state="disabled")
            tabControl.tab(1, state="hidden")
            compareButton.pack_forget()
            levButton.pack_forget()
            showGraphButton1.pack_forget()
            frontLabelRdy.place_forget()
            TVV2.pack_forget()
        else:
            return None
        
    dlg =  filedialog.askopenfilenames() #Avab faili
    
    if dlg=='':
        return messagebox.showinfo("Faili avamine", "Ühtegi faili ei valitud või fail on tühi. Vali MusicXML-fail")
    elif  dlg[0].lower().endswith(('.musicxml', '.mxl')) == False:
        return messagebox.showinfo("Vale fail", "Sisestatud fail on vale, sisesta MusicXML-fail.")
    
    start_time = time.time()
    
    if note1 != '': #Kõik indeksiga 2 - 2. noot
        note2 = dlg[0]
        noteName = str(os.path.basename(dlg[0]))
        n2 = analyze(get_partstream(note2), noteName)
        TVõ2.config(state='normal')
        TVõ2.insert(END, "2.NOODISTUS" + '\n')
        edit_text(n2, TVõ2)
        frontLabelRdy.place(relx=0.5, rely=0.9, anchor=CENTER)
        return check_compare() 
    
    else: #Kõik indexiga 1 - 1. noot
        note1 = dlg[0] #Notepath
        noteName = str(os.path.basename(dlg[0]))
        n1 = analyze(get_partstream(note1), noteName)  #Analyzed form of note
        tabControl.tab(1, state="normal")
        TVõ1.config(state='normal')
        TVõ1.insert(END, "1.NOODISTUS"+ '\n')
        return edit_text(n1, TVõ1)

#Kontrollib seda, et logi faili ei tekiks duplikaat noote
def check_file_write(data):
    file=open("log.txt",'r')
    for elem in file:
        if data in elem:
            return False
    file.close()
    return True

#Converdib XML faili ja jagab noodi instrumendi osade järgi ära
def get_partstream(file):
    if file =='':
        return messagebox.showinfo("Faili viga", "Sisestatud fail on on vigane.")
    else:
        f = converter.parseFile(file)
        partStream = f.parts.stream()
    return partStream

#Konstrueerib suure listi, kus on noodi partiide kohta sõnastikud ehk strukturiseerib noodi andmehoidja.
def analyze(note, noteName):
    allNote = [] #Kõik partide dictionarid tulevad siia
    allNote.append(noteName)
    for el in note.elements: #Iga part eraldi el = PartStaff
        partList = {}
        partList['partName'] = el.partName 
        partList['sharps'] = el[1].keySignature.sharps #1. taktist saab helistiku märgid kätte.
        partList['bpm'] = "Puudub"
        if partList['sharps'] == 0:
            partList['key'] = "C major/a minor"
        else:
            try:
                partList['key'] = el.analyze("key").name #MusicXML enda tuvastusalgoritm (ei ole alati täpne)
            except:
                partList['key'] = "Ei suutnud tuvastada."
        if el[1].timeSignature != None:
            partList['tempo'] = (el[1].timeSignature.numerator, el[1].timeSignature.denominator)
        else:
            partList['tempo'] =(4,4)
        for elem in el[1]:
            if "MetronomeMark" in str(elem):
                partList['bpm'] = str(elem.number) + ' bpm'
        partList['clef'] = el[1].clef.name
        partList['measures'] = get_measure_info(el, partList)
        
        allNote.append(partList)
    allNote.append(allNote[1].get('melodynotes'))
    allNote.append(allNote[1].get('intervals'))
   
    return allNote

#Leiab kõik taktid ja takti sisu ning paneb need sõnastikku, sõnastikud lähevad listi
def get_measure_info(part, partList):
    measures = [] #List, kuhu lähevad measure dictid:
    chords = []
    rests = []
    notes = []
    allInfo = []
    melNotes = []
    notesDur = 0
    restsDur = 0
    for e in part.getElementsByClass('Measure'):
        newMeasure = {}        
        newMeasure[e.number] = list(e.notesAndRests.elements)
        measureInt =[]
        if e.hasVoices():
            for voice in e.getElementsByClass('Voice'):
                for v in voice.elements:
                    newMeasure[e.number].append(v)
        for elem in newMeasure[e.number]:
            if elem.isNote:
                notes.append(elem.nameWithOctave)
                notesDur+=elem.duration.quarterLength
                allInfo.append(elem)
                measureInt.append(elem)
                melNotes.append(elem)
            elif elem.isChord and '<music21.harmony.ChordSymbol' not in str(elem):
                chords.append(elem.pitchedCommonName)
                notesDur+=elem.duration.quarterLength
                measureInt.append(elem.notes[-1])
                allInfo.append(elem.notes[-1])
                melNotes.append(elem.notes[-1])
                for c in elem.notes:
                    notes.append(c.nameWithOctave)
            elif elem.isRest:
                restsDur+=elem.duration.quarterLength
        newMeasure[e.number].append(measureInt) 
        measures.append(newMeasure)
    rests.append(notesDur)
    rests.append(restsDur)
    partList['melodynotes'] = melNotes
    partList['notes'] = notes
    partList['chords'] = chords
    partList['rests'] = rests
    partList['intervals'] = find_intervals(allInfo)
    
    return measures

#Taandab kõik intervallid 0-12 pooltooni vahemikku
def check_semitones1(st_inter, intervals):
    if 24 > st_inter > 12:
        st_inter = st_inter-12
        intervals.append(st_inter)
    elif 36 > st_inter > 24:
        st_inter = st_inter-24
        intervals.append(st_inter)
    elif 48 > st_inter > 36:
        st_inter = st_inter-36
        intervals.append(st_inter)
    elif -24 < st_inter < -12:
        st_inter = st_inter+12
        intervals.append(st_inter)
    elif -36 < st_inter < -24:
        st_inter = st_inter+24
        intervals.append(st_inter)
    elif -48 < st_inter < -36:
        st_inter = st_inter+36
        intervals.append(st_inter)
    else:
        intervals.append(st_inter)

#Taandab kõik intervallid 0-12 pooltooni vahemikku
def check_semitones(st_inter, intervals):
    if st_inter > 12:
        st_inter = st_inter % 12  
    elif st_inter < -12:
        st_inter = st_inter % -12
    intervals.append(st_inter)
    
        
#Tuvastab nootide vahelised intervallid  
def find_intervals(allInfo):
    intervals= []
    i=1 #Alustan 2. noodist, sest pean alati kontrollima, kas eelmine noot on noot või mitte.
    while i != len(allInfo) and len(allInfo) != 0 and len(allInfo) != 1:
        if allInfo[i-1].isNote and allInfo[i].isNote:
            inter = interval.Interval(noteStart=allInfo[i-1], noteEnd=allInfo[i]).semitones
            check_semitones(inter,intervals)
            
        i+=1
    return intervals

#Saame instrumentide nimed kätte partiidest
def get_instruments(note):
    lst=[]
    for i in range (len(note)):
        if 'partName' in note[i]:
            lst.append(note[i].get('partName'))
    return lst

#Saame tõenäoliseima noodi helistiku
def get_key(note):
    lst=[]
    for i in range (len(note)):
        if 'key' in note[i]:
            lst.append(note[i].get('key'))
    if lst == []:
        return "Ei suutnud helistikku määrata."
    else:
        return str(max(set(lst), key = lst.count))
    
#Saame noodis esinevate taktide arvu
def get_bars_count(note):
    return len(note[1].get('measures'))

#Saame kätte enimkasutatud nootide, intervallide jne info
def get_elements_info(note, name):
    intervalDict = {0:"P0", 1:"v2", 2:"S2",
                    3:"v3", 4:"S3", 5:"P4", 6:"Tritoon",
                    7:"P5", 8:"v6", 9:"S6", 10:"v7",
                    11: "S7", 12:"P8"}
    count= 0
    mostUsed = "Puudub"
    lst = []
    for i in range(0,len(note)):
        elements = note[i].get(name)
        s = len(elements)
        count+=s
        lst+=elements
    
    if lst != []:
        mostUsed = max(set(lst), key=lst.count)
    if name=="intervals":
        mostUsed = intervalDict.get(mostUsed)
    
    return (count, mostUsed)

#Saame teada noodis olevate pauside protsentuaalse koguse
def get_rests_info(note, name):
    notesDur =0
    restsDur =0
    wholeDur =0
    for elem in note:
        if name in elem:
            elements = elem.get(name)
            notesDur+=elements[0]
            restsDur+=elements[1]
    wholeDur+= notesDur + restsDur
    percent = (restsDur*100)/wholeDur
    return str(round(percent,1))

#Saame kätte noodi tempo
def get_tempo(note):
    return note[1].get('bpm')


#Kontrollib, kas valitud noodid on võrlduseks kõlblikud
def check_compare():
    global n1, n2, compareButton, tab2
    if n1 != '' and n2 !='':
        compareButton.pack(side=BOTTOM)
        return levButton.pack(side=BOTTOM)
    else:
        return messagebox.showinfo("Võrdlus katkestatud", "Failid on tühjad või ebasobivad. Vali MusicXML-fail.")
    
# ----- VÕRDLUS -----
#Võrdluse käivitamise tingimuste kontroll, algoritmi käivitamine ja info kuvamine ekraanile 
def compare():
    global n1, n2, entryField, TVV, showGraphButton1,  lev_dup_series, TVV2, oct_dist_button
    
    
    TVV.config(state="normal")
    TVV.delete('1.0', END)
    showGraphButton1.pack_forget()
    
    entryInt = entryField.get()
    
    try:
        entryInt = int(entryInt)
    except:
        return messagebox.showinfo("Võrdlus katkestatud", "Sisestatud noodi järgnevuse arv pole korrektne.")
        
    #Meloodia intervallid
    melIntervals1 = n1[-1] 
    melIntervals2 = n2[-1]
    
    #Meloodia noodid
    allNotes1 = n1[-2] 
    allNotes2 = n2[-2]
   
    if entryInt > len(allNotes1) and entryInt > len(allNotes2):
        return messagebox.showinfo("Võrdlus katkestatud", "Sisestatud noodi järgnevuse arv ületab noodistuse nootide arvu ühes noodis.")
    
    similarInts = interval_pattern_finder(intervals_to_letters
                           (melIntervals1), intervals_to_letters(melIntervals2), entryInt, allNotes1, allNotes2, 2)
    
    
    transLevs = get_distance(allNotes1, allNotes2, lev_dup_series,oct_dist_button)
   
    if all(similarInts) or all(similarNotes):
        if lev_dup_series.get():
            TVV.insert(END, "[Ü] Kahe meloodia vaheline väikseim teisenduskaugus on " + str(min(transLevs)) +", kui meloodiat transponeeriti " + str(transLevs.index(min(transLevs))) + " pooltooni üles." + '\n')
        else:
            TVV.insert(END, "Kahe meloodia vaheline väikseim teisenduskaugus on " + str(min(transLevs)) +", kui meloodiat transponeeriti " + str(transLevs.index(min(transLevs))) + " pooltooni üles." + '\n')
        if similarInts !=[]:
            if similarInts[0] !=[] and similarInts[1] !=[]:
                inf1 = print_info(similarInts[0])
                inf2 = print_info(similarInts[1])
                TVV.insert(END,"Leiti " + str(len(similarInts[0])) + " sarnast " +str(entryInt)+ "-noodilist intervalli järgnevust." + '\n' +
                   "1.noodistus: " + '\n' + ('\n'.join(map(str, inf1))) + '\n' +
                   "2.noodistus: " + "\n" + ('\n'.join(map(str, inf2))) + '\n')
                showGraphButton1.configure(command=(lambda:show_graph(allNotes1, allNotes2, similarInts[2])))
                showGraphButton1.pack()
        else:
            TVV.insert(END,"Sarnaseid meloodia järgnevusi ei ole." + '\n')
    else:
        TVV.insert(END,"Sarnaseid meloodia järgnevusi ei ole." + '\n')
    
    #Salvestame logi faili
    save_to_file(n1[0], allNotes1)
    save_to_file(n2[0], allNotes2)
    
    return TVV.config(state="disabled")

# --- INTERVALLI JÄRGNEVUSTE OTSIMINE ---
# Teostab noodivahelist võrdlust. Väljastab sarnased meloodia järgnevused ja nende asukohad nootides
def interval_pattern_finder(lst1, lst2, n, allNotes1, allNotes2, variable):
    #Kõik intervalli järgnevused, mis esinevad mõlemas noodis
    similarities = find_similarities(n, lst1, lst2, variable)

    #Leiab kõik unikaalsed intervalli järgnevused, mis esinevad mõlemas noodis
    uniq_sim = remove_duplicates(similarities)
    
    #Leiame iga noodi kohta, mis positsioonidel on antud järgnevuste duplikaatide (indexid)
    dupli1= []
    dupli2 =[]
    for elem in uniq_sim:
        dupli1.append(list_duplicates_of(lst1, elem))
        dupli2.append(list_duplicates_of(lst2, elem))
    graph_dots ={}
    
    #Koostab graafiku punktid kõikide sarnaste intervalli järgnevuste kattuvustega
    for i in range(len(dupli1)):
        key = uniq_sim[i]
        values_lst_x =[]
        values_lst_y =[]
        for x,y in itertools.product(dupli1[i],dupli2[i]):
            values_lst_x.append(x)
            values_lst_y.append(y)
        graph_dots[key] = (values_lst_x, values_lst_y)
    
    #Siia leian sarnased meloodiad
    similarity1 = find_similar_melodies(dupli1, allNotes1, n)
    similarity2 = find_similar_melodies(dupli2, allNotes2, n)
    
    if len(similarity1)==0 and len(similarity2)==0 :
        return []
    else:
        return (similarity1, similarity2, graph_dots)

#Teisendab intervallid tähtväärtusteks, et suudaks ära tunda intervallide järjekorda ühes pikas jadas.
def intervals_to_letters(lst):
    nd = {0: "A", 1:"B", 2:"C", 3:"D", 4:"E", 5: "F", 6:"G", 7:"H", 8:"I", 9:"J", 10:"K", 11:"L", 12: "M",
       -1:"N", -2:"O", -3:"P", -4:"Q", -5: "R", -6:"S", -7:"Z", -8:"T", -9:"U", -10:"V", -11:"W", -12: "X"}
    uusl = []
    for el in lst:
        if el in nd:
            uusl.append(nd.get(el))
        else:
            #Kui ei suuda tuvastada, siis lisab tundmatu märgi
            uusl.append("Y")
    llst = "".join(str(x) for x in uusl)
    return llst

#Teisendab  noodid pooltoonide ja oktavite paarideks
def note_to_pairs(notes):
    uusl = []
    for e in notes:
        pitchClass = e.pitch.pitchClass
        noteOct = e.octave
        uusl.append((pitchClass, noteOct)) 
    return uusl

#Leiab kõik sarnased nootide järgnevused intervalli järgi
def find_similarities(n, lst1, lst2, variable):
    similarities = []
    i=0
    if len(lst1) <= len(lst2):
        while i+(n-variable) != len(lst1):
            newlst = lst1[i:i+(n-(variable-1))]
            all = re.findall(newlst, lst2)
            i+=1
            if all != []:
                similarities.append(all)
    else:
        while i+(n-variable) != len(lst2):
            newlst = lst2[i:i+(n-(variable-1))] 
            all = re.findall(newlst, lst1)
            i+=1
            if all != []:
                similarities.append(all)
    return similarities

#Kogub kokku kõik unikaalsed sarnased intervallide järgnevused
def remove_duplicates(lst):
    uniq_sim= []
    for elem in lst:
        if elem[0] in uniq_sim:
            pass
        else:
            uniq_sim.append(elem[0])
    return uniq_sim

#Leiab listi duplikaatide indeksid
#seq - intervallide list tähtedes ['AAOBCF...']
#elem - konkreetne leitud järgnevus ['AAO']
#RETURN - asukohad intervalli tähtede jadas -< [0]
def list_duplicates_of(seq, elem):
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(elem, start_at+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs


#Leiab kõik kahe noodi sarnased meloodia järgnevused intervallide järgi  
def find_similar_melodies(sim_index, allNotes, n):
    final_notes =[]
    for lst in sim_index:
        notes =[]
        for i in lst:
            n_sim = []
            j = i
            k = 0
            while j + k != i + n:
                n_sim.append(allNotes[j+k].nameWithOctave)
                k+=1
            notes.append(n_sim)
        final_notes.append(notes)
    return final_notes

# --- KAUGUS ---
#Transponeerib meloodia noodid ühe pooltooni võrra

def get_distance(allNotes1, allNotes2, lev_dup_series, oct_dist_button):
     
    pairs1 = note_to_pairs(allNotes1)
    pairs2 = note_to_pairs(allNotes2)
    #Kui checkbox in aktiivne
    if lev_dup_series.get():
        pairs1 = [x[0] for x in groupby(pairs1)]
        pairs2 = [x[0] for x in groupby(pairs2)]
    
    #Arvestab noodi oktavit
    if oct_dist_button.get():
        lev_dp = modified_lev_dist_oct(pairs1, pairs2)
    else:
        lev_dp = modified_lev_dist(pairs1, pairs2)
        
    transLevs = []
    transLevs.append(lev_dp)
    for i in range(1, 11):
        transposed = transpose_notes(allNotes2, i)
        transPairs1 = note_to_pairs(allNotes1)
        transPairs2 = note_to_pairs(transposed)
        if lev_dup_series.get():
            transPairs1 = [x[0] for x in groupby(transPairs1)]
            transPairs2 = [x[0] for x in groupby(transPairs2)]
        if oct_dist_button.get():
            transLevs.append(modified_lev_dist_oct(transPairs1, transPairs2))
        else:
            transLevs.append(modified_lev_dist(transPairs1, transPairs2))
    
    return transLevs

def transpose_notes(notes, step):
    transposed = []
    for elem in notes:
        transposed.append(elem.transpose(step))
    return transposed

def calculate_dist_oct(x1, x2):
    if x1[0] < x2[0] and x1[1] > x2[1]: #x1: (1,4), x2: (11,2) = 14 V (2,4) ja (9,3) = 5
        return 12*(x1[1]-x2[1])-(x2[0]-x1[0])
    elif x1[0] < x2[0] and x1[1]< x2[1]: #x1: (1,1), x2: (11,2) = 22
        return (x2[0]-x1[0]) + 12*(x2[1]-x1[1])
    elif x1[0] > x2[0] and x1[1] > x2[1]:# x1: (5, 3), x2: (2,1) = 25
        return (x1[0]-x2[0]) + 12*(x1[1]-x2[1])
    elif x1[0] > x2[0] and x1[1] < x2[1]: # x1: (5, 3), x2: (2,4) = 9
        return 12*(x2[1]-x1[1])-(x1[0]-x2[0])
#Funktsioon arvestab oktaveid
def modified_lev_dist_oct(notes1, notes2):
    levdist = 0
    
    if len(notes1) >= len(notes2):
        diff = len(notes1)-len(notes2)
        for i in range(0, len(notes2)):
            x1 = notes1[i]
            x2 = notes2[i]
            if x1[1] == x2[1]:
                levdist += abs(x1[0] - x2[0])
            else:
                if x1[0] == x2[0]:
                    levdist += abs(x1[1]-x2[1])*12
                else:
                    levdist += calculate_dist_oct(x1, x2)
            
        levdist +=diff
        return levdist
    else:
        diff = len(notes2)-len(notes1)
        for i in range(0, len(notes1)):
            x1 = notes1[i]
            x2 = notes2[i]
            if x1[1] == x2[1]:
                levdist += abs(x1[0] - x2[0])
            else:
                if x1[0] == x2[0]:
                    levdist += abs(x1[1]-x2[1])*12
                else:
                    levdist += calculate_dist_oct(x1, x2)
        
        levdist +=diff
        return levdist


#Funktsioon arvestab oktaveid
#Oktaveid ei arvesta
def modified_lev_dist(notes1, notes2):
   
    levdist = 0
    
    if len(notes1) >= len(notes2):
        diff = len(notes1)-len(notes2)
        for i in range(0, len(notes2)):
            x1 = notes1[i]
            x2 = notes2[i]
            if x1[0] == x2[0]:
                levdist += 0
            else:
                if x1[1] == x2[1]:
                    levdist += abs(x1[0]-x2[0])
                else:
                    if 12-x1[0] == x2[0]:
                        levdist += abs(x1[0]-x2[0])
                    else:
                        k = abs(x1[0]-x2[0])
                        levdist += min(k, 12-k)
        levdist +=diff
        return levdist
    else:
        diff = len(notes2)-len(notes1)
        for i in range(0, len(notes1)):
            x1 = notes1[i]
            x2 = notes2[i]
            if x1[0] == x2[0]:
                levdist += 0
            else:
                if x1[1] == x2[1]:
                    levdist += abs(x1[0]-x2[0])
                else:
                    if 12-x1[0] == x2[0]:
                        levdist += abs(x1[0]-x2[0])
                    else:
                        k = abs(x1[0]-x2[0])
                        levdist += min(k, 12-k)
            
        levdist +=diff
        return levdist

#Varasemate nootidega ja võrreldava noodiga lev kauguste leidmine
def lev_data_comparison():
    f = open('log.txt', 'r')
    data = f.readlines()
    if len(data) > 15:
        result = messagebox.askokcancel("Diginootide meloodiaanalüsaator",
                                        "Logifailis on üle 15 kirje, mistõttu programmi töö võib olla aeglane. Soovituslik on logi faili puhastada. Kas jätkan analüüsi?")
        if result == True:
            lev_data_analyze()
        else:
            messagebox.showinfo("Diginootide meloodiaanalüsaator", "Analüüs katkestatud.")
            return  
    else:
        lev_data_analyze()
        
def convert_note_names(lst):
    newlst = []
    for elem in lst:
        newlst.append(elem.nameWithOctave)
    return newlst

def lev_data_analyze():
    global n1, n2, lev_dup_series,oct_dist_button
    start_time2 = time.time()
    levDistances ={}
    with open('log.txt', 'r') as f1:
        if os.stat("log.txt").st_size == 0:
            return  messagebox.showinfo("Diginootide meloodiaanalüsaator",
                                        "Logi fail on tühi. Varasemad noodistuste analüüsid puuduvad.")
        for elem in f1:
            l = ast.literal_eval(elem)
            if n1[0] != l[0] and convert_note_names(n1[-2]) != l[-1]:
                newNotes =[]
                for e in l[-1]:
                    newNotes.append(note.Note(e))
                levDistances[l[0]] = get_distance(n1[-2], newNotes, lev_dup_series,oct_dist_button)
    mini = min(levDistances, key=levDistances.get)
    result = str(n1[0]) +" noodiga on sarnaseim "  + str(mini) + " kaugusega " + str(min(levDistances[mini])) + ", kui võrreldavat nooti transponeeriti " + str(levDistances[mini].index(min(levDistances[mini]))) + " tooni üles." 
    TVV2.pack(side=TOP, fill=Y)
    TVV2.config(state="normal")
    TVV2.delete('1.0', END)
    
    if lev_dup_series.get():
        TVV2.insert(1.0, "[Ü] " + str(result) + '\n')
    else:
        TVV2.insert(1.0, str(result) + '\n')
    TVV2.config(state="disabled")
    print("--- %s seconds ---" % (time.time() - start_time2))
    return None
    
def save_to_file(noteName, pairs):
    if check_file_write(noteName):
        lst = []
        lst.append(noteName)
        lst.append(convert_notes_to_string(pairs))
        with open('log.txt', 'a') as f:
            f.write(str(lst) + '\n')
        f.close()
    return

def convert_notes_to_string(notes):
    noteStrings =[]
    for elem in notes:
        noteStrings.append(elem.nameWithOctave)
    return noteStrings
           
# --- GRAAF ---
#Moodustab meloodia järgnevuste graafi
def show_graph(all1, all2, dot_lst):
    
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1, aspect=1)
    ax.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
    ax.set_title("Ühtimispunktid noodistustes", fontsize=20, verticalalignment='bottom')
    ax.set_xlabel("2.noodistus (ühtimiskoha noodi asukoha indeks)")
    ax.set_ylabel("1.noodistus (ühtimiskoha noodi asukoha indeks)")
    if len(all1)>len(all2):
        ax.xaxis.set_major_locator(MultipleLocator(len(all1)))
        ax.xaxis.set_minor_locator(AutoMinorLocator(len(all1)/10))
        ax.yaxis.set_major_locator(MultipleLocator(len(all1)))
        ax.yaxis.set_minor_locator(AutoMinorLocator(len(all1)/10))
        ax.set_xlim(0, len(all1))
        ax.set_ylim(0, len(all1))
    else:
        ax.xaxis.set_major_locator(MultipleLocator(len(all2)))
        ax.xaxis.set_minor_locator(AutoMinorLocator(len(all2)/10))
        ax.yaxis.set_major_locator(MultipleLocator(len(all2)))
        ax.yaxis.set_minor_locator(AutoMinorLocator(len(all2)/10))
        ax.set_xlim(0, len(all2))
        ax.set_ylim(0, len(all2))
   
    counter = []
   
    for i in range(len(dot_lst)):
        counter.append(i+1)        
    for elem in dot_lst:
        values = dot_lst[elem]
        x = values[0]
        y = values[1]
        ax.scatter(x,y, color=numpy.random.rand(3,))
    
    ax.legend(counter, bbox_to_anchor=(1, 1), loc='upper left')
    return plt.show()


def print_info(info):
    fin_info =[]
    for index, name in enumerate(info):
        fin_info.append('{}{}{}'.format(index+1, " - ", name))
    return fin_info

def get_notes_info(note):
    mostUsed = "Puudub"
    lst = []
    for elem in note:
        n = elem.nameWithOctave
        lst.append(n)
    if lst != []:
        mostUsed = max(set(lst), key=lst.count)
    return (len(lst), mostUsed)

def get_chords_info(note, name):
    mostUsed = "Puudub"
    lst = []
    for e in note[name]:
        lst.append(e)
    if lst != []:
        mostUsed = max(set(lst), key=lst.count)
    return (len(lst), mostUsed)
#Kuvab teksti GUI lahtrisse
def edit_text(note, textbox):
    global start_time
    
    textbox.config(state='normal')
    
    title = "Noodifaili nimi: " + str(note[0]) + '\n'
    bpm = "Tempo: " + str(get_tempo(note)) +'\n'
    partsCount = "Noodi partiide arv: " + str(len(note)-3) + '\n'
    instruments = "Instrumendid: " + str(' '.join(get_instruments(note))) + '\n'
    noteKey = "Arvatav helistik: " + get_key(note) + '\n'
    bar = "Taktimõõt: " + str(note[1].get('tempo')) + '\n'
    barsCount = "Meloodia partii taktide koguarv: " + str(get_bars_count(note)) +'\n'
    
    notesInfo = get_notes_info(note[-2])
    chordsInfo = get_chords_info(note[1], 'chords')
    
    notesPerPart ="Meloodia nootide koguarv: " + str(notesInfo[0]) + '\n' + "Kõige sagedasem meloodia noot: " + str(notesInfo[1]) + '\n'
    
    chordsPerPart = "Meloodia kooskõlade koguarv: " + str(chordsInfo[0]) + '\n' + "Kõige sagedasem meloodia kooskõla: " + str(chordsInfo[1]) + '\n'
    
    restsPerPart = "Pauside osakaal " + get_rests_info(note, 'rests') + "%" + '\n'
    
    #Mõõdab programmi võrdluse algoritmi töö aega
    print("--- %s seconds ---" % (time.time() - start_time))
    
    textbox.insert(END, title + bpm + instruments + partsCount + noteKey + bar +
                   barsCount + notesPerPart + chordsPerPart + restsPerPart )
    
    return textbox.config(state='disabled')

#Kuvab programmi juhise akna
def on_help():
    return messagebox.showinfo("Programmi juhis","Programm on mõeldud diginootide meloodiate analüüsimiseks ja võrdlemiseks." + '\n'+
    "Vali programmi kaks MusicXML-faili (.mxl või .musicxml). Pärast seda avaneb mõlema faili kohta info lahtrisse 'Võrdlus'." + '\n'+
    "Seal lahtris oma võimalik tuvastada kahe noodistuse pikimaid sarnaseid meloodiajärgnevusi ning teisenduskaugusi." + '\n' +
    "Sisestades programmi arvu, kui pikka sarnast noodijärgnevust leida soovid, avaneb keskmisesse lahtrisse mõlema noodistuse saransed noodijärgnevused"+
    "ning võimalus kujutada ka järgnevuste asukohti graafiliselt nupul 'Intervallide graafik'. " + '\n' +
                                 "Pärast seda saab saadud tulemused salvestada vabalt valitud kohta .pdf/.png näol." +
                               "Analüüsi tulemused on võimalik salvestada .txt faili. - Fail-> Salvesta tulemus.")
#Salvestab võrdluse tulemused                                   
def on_save():
    global fileName
    text2save = str(TVõ1.get(1.0,END)) +str(TVõ2.get(1.0,END)) + str(TVV.get(1.0, END)) + str(str(TVV2.get(1.0, END)))
    if len(text2save) < 5:
        messagebox.showinfo("Diginootide meloodiaanalüsaator", "Võrdlust pole teostatud.")
        return 
    f = filedialog.asksaveasfile(mode='w',defaultextension=".txt")
    if f is None: 
        return
    f.write(text2save)
    fileName = f.name
    f.close()
    messagebox.showinfo("Diginootide meloodiaanalüsaator", "Faili salvestamine õnnestus asukohta " + str(fileName))
    return

def on_delete_log():
    result = messagebox.askokcancel("Diginootide meloodiaanalüsaator","Kas oled kindel, et soovid logifaili ajalugu kustutada?")
    if result == True:
        open("log.txt", "w").close()
        messagebox.showinfo("Diginootide meloodiaanalüsaator", "Logifaili ajalugu edukalt kustutatud.")
        return 

#GUI loomine ja programmi käivitus
root = Tk()
root.minsize (200, 200)
root.title("Diginootide meloodiaanalüsaator")
frame = Frame(root)
frame.pack(expand="true", fill="both")
note1 = ''
note2 = ''
n1 =''
n2 =''
n1txtbox = ''
menubar = Menu(frame)
fileMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Fail", menu=fileMenu)
fileMenu.add_command(label="Abi", command = on_help)
fileMenu.add_command(label="Salvesta tulemus", command = on_save)
fileMenu.add_command(label="Kustuta logifaili sisu", command = on_delete_log)

tabControl = ttk.Notebook(frame)
tab1 = ttk.Frame(tabControl) 
tabControl.add(tab1, text = "Esileht")

frame1 = Frame(tab1, bg="SteelBlue1")
frame1.pack(expand="true", fill="both")


tab2 = ttk.Frame(tabControl)
tabControl.add(tab2, text = "Võrdlus", state="hidden") 

tabControl.pack(expan = 1, fill ="both")

frontLabel = Label(frame1, text="Diginootide meloodiaanalüsaator", font=("Open Sans",15 ), bg="SteelBlue1", fg="White")
frontLabel.place(relx=0.5, rely=0.1, anchor=CENTER)

frontLabelRdy = Label(frame1, text="Diginoodid on võrdluseks valmis - vajuta Võrdlus lahtrile.", font=("Open Sans", 20), bg="SteelBlue1", fg="White")
frontLabelRdy.place_forget()

photo1 = PhotoImage(file="btn.png")
photo2 = PhotoImage(file="compareBT2.png")

openFileButton = Button(frame1, command=on_open,     
                justify = "center", bg="SteelBlue1", bd=0, image=photo1,
                anchor="center", activebackground= "SteelBlue1", text="Vali diginoot, mida analüüsida")

openFileButton.place(relx=0.5, rely=0.5, anchor=CENTER)


compareButton = Button(tab2, command=compare,     
                justify = "center", bd=0,
                anchor="s",image=photo2, text="Võrdle", state="normal")

compareButton.place_forget() 

levButton = Button(tab2, command=lev_data_comparison,     
                justify = "center", bd=3,
                anchor="s", text="Väikseim kaugus varasemalt võrreldud noodistustega", state="normal")

levButton.place_forget() 


showGraphButton1 = Button(tab2,    
                justify = "center", bd=6,
                anchor="s", text="Järgnevuste graafik", state="normal")
showGraphButton1.pack_forget()

TVõ1 = Text(tab2, height=20, width=40, bd=4, bg='whitesmoke', state='disabled', font=("Open sans", 12), padx=50, wrap = WORD)
TVõ2 = Text(tab2, height=20, width=40, bd=4, bg='whitesmoke', state='disabled', font=("Open sans", 12), padx=50, wrap = WORD)
TVV = Text(tab2, height=10, width=40, bd=4, bg='white', state='disabled', font=("Open sans", 12), padx=50, wrap = WORD ,spacing1=5, spacing2=10)
TVV2 = Text(tab2, height=4, width=40, bd=4, bg='white', state='disabled', font=("Open sans", 12), padx=50, wrap = WORD ,spacing1=5, spacing2=10)

compareFrame = Frame(tab2)
compareFrame.pack()
entryLabel = Label(compareFrame, text="Vali, kui pikka noodijärgevust soovid võrrelda:", font=("Open Sans",12))
entryLabel.pack()
entryField = Entry(compareFrame)
entryField.pack(side=TOP, fill=Y)

lev_dup_series = IntVar()
oct_dist_button = IntVar()

checkBtn1 = Checkbutton(tab2, text="Ühenda järjest korduvad noodid (teisenduskaugus)", variable=lev_dup_series, onvalue = 1, offvalue = 0)
checkBtn1.pack()

checkBtn2 = Checkbutton(tab2, text="Arvesta nootide oktavit (teisenduskaugus)", variable=oct_dist_button, onvalue = 1, offvalue = 0)
checkBtn2.pack()

TVõ1.pack(side=LEFT, fill=Y)
TVõ2.pack(side=RIGHT, fill=Y)
TVV.pack(side=TOP, fill=Y)
TVV2.pack_forget()

TVõ1.insert(END, n1)
TVõ2.insert(END, n2)

if n1txtbox != "":
    TVV.insert(END, n1txtbox)

root.config(menu=menubar)
root.mainloop()
