#! pip install spire.doc
#! pip install Spire.XLS
import pandas as pd
from spire.doc import *
from spire.doc.common import *
from spire.xls import *
from spire.xls.common import *
from NER import cleanText
import requests 
class wordDoc(): # using python-docx
  def __init__(self, wordDoc,saveFolder):
    self.wordDoc = wordDoc
    self.saveFolder = saveFolder
  def openFile(self):
    document = Document()
    return document.LoadFromFile(self.wordDoc)
  def extractTextByPage(self):
    # reference: https://medium.com/@alice.yang_10652/extract-text-from-word-documents-with-python-a-comprehensive-guide-95a67e23c35c#:~:text=containing%20specific%20content.-,Spire.,each%20paragraph%20using%20the%20Paragraph.
    json = {}
    #doc = self.openFile()
    # Create an object of the FixedLayoutDocument class and pass the Document object to the class constructor as a parameter
    try:
      doc = Document()
      doc.LoadFromFile(self.wordDoc)
    except:
      response = requests.get(self.wordDoc)
      name = self.wordDoc.split("/")[-1]
      with open(self.saveFolder+"/" + name, "wb") as temp_file:  # Create a temporary file to store the downloaded data
        temp_file.write(response.content)  
      doc = Document()
      doc.LoadFromFile(self.saveFolder+"/" + name)
    text = doc.GetText()
    return text
  def extractTableAsText(self):
    getDoc = ''
    try:
      # reference:
      # https://www.e-iceblue.com/Tutorials/Python/Spire.Doc-for-Python/Program-Guide/Table/Python-Extract-Tables-from-Word-Documents.html?gad_source=1&gclid=Cj0KCQiA6Ou5BhCrARIsAPoTxrCj3XSsQsDziwqE8BmVlOs12KneOlvtKnn5YsDruxK_2T_UUhjw6NYaAtJhEALw_wcB
      doc = Document()
      doc.LoadFromFile(self.wordDoc)
      getDoc = "have document"
    except:
      response = requests.get(self.wordDoc)
      name = self.wordDoc.split("/")[-1]
      with open(self.saveFolder+"/" + name, "wb") as temp_file:  # Create a temporary file to store the downloaded data
        temp_file.write(response.content)  
      doc = Document()
      doc.LoadFromFile(self.saveFolder+"/" + name)  
      getDoc = "have document"
    json = {}
    if len(getDoc) > 0:
      # Loop through the sections
      for s in range(doc.Sections.Count):
        # Get a section
          section = doc.Sections.get_Item(s)
          # Get the tables in the section
          json["Section" + str(s)] = {}
          tables = section.Tables
          # Loop through the tables
          for i in range(0, tables.Count):
              # Get a table
              table = tables.get_Item(i)
              # Initialize a string to store the table data
              tableData = ''
              # Loop through the rows of the table
              for j in range(0, table.Rows.Count):
                  # Loop through the cells of the row
                  for k in range(0, table.Rows.get_Item(j).Cells.Count):
                      # Get a cell
                      cell = table.Rows.get_Item(j).Cells.get_Item(k)
                      # Get the text in the cell
                      cellText = ''
                      for para in range(cell.Paragraphs.Count):
                          paragraphText = cell.Paragraphs.get_Item(para).Text
                          cellText += (paragraphText + ' ')
                      # Add the text to the string
                      tableData += cellText
                      if k < table.Rows.get_Item(j).Cells.Count - 1:
                          tableData += '\t'
                  # Add a new line
                  tableData += '\n'
              json["Section" + str(s)]["Table"+str(i)] = tableData
    return json
  def extractTableAsList(self):
    tables = []
    try:
      doc = Document()
      doc.LoadFromFile(self.wordDoc)
    except:
      response = requests.get(self.wordDoc)
      name = self.wordDoc.split("/")[-1]
      with open(os.path.join(self.saveFolder, name), "wb") as f:
        f.write(response.content)
      doc = Document()
      doc.LoadFromFile(os.path.join(self.saveFolder, name))

    for s in range(doc.Sections.Count):
      section = doc.Sections.get_Item(s)
      for i in range(section.Tables.Count):
        table = section.Tables.get_Item(i)
        table_data = []
        for row in range(table.Rows.Count):
          row_data = []
          for cell in range(table.Rows.get_Item(row).Cells.Count):
            cell_obj = table.Rows.get_Item(row).Cells.get_Item(cell)
            cell_text = ""
            for p in range(cell_obj.Paragraphs.Count):
              cell_text += cell_obj.Paragraphs.get_Item(p).Text.strip() + " "
            row_data.append(cell_text.strip())
          table_data.append(row_data)
        tables.append(table_data)
    return tables  
  def extractTableAsExcel(self):
    getDoc = ''
    try:
      # reference:
      # https://www.e-iceblue.com/Tutorials/Python/Spire.Doc-for-Python/Program-Guide/Table/Python-Extract-Tables-from-Word-Documents.html?gad_source=1&gclid=Cj0KCQiA6Ou5BhCrARIsAPoTxrCj3XSsQsDziwqE8BmVlOs12KneOlvtKnn5YsDruxK_2T_UUhjw6NYaAtJhEALw_wcB
      doc = Document()
      doc.LoadFromFile(self.wordDoc)
      getDoc = "have document"
    except:
      response = requests.get(self.wordDoc)
      name = self.wordDoc.split("/")[-1]
      with open(self.saveFolder+"/" + name, "wb") as temp_file:  # Create a temporary file to store the downloaded data
        temp_file.write(response.content)  
      doc = Document()
      doc.LoadFromFile(self.saveFolder+"/" + name)  
      getDoc = "have document"
    if len(getDoc) > 0:
      try:
        # Create an instance of Workbook
        wb = Workbook()
        wb.Worksheets.Clear()

        # Loop through sections in the document
        for i in range(doc.Sections.Count):
            # Get a section
            section = doc.Sections.get_Item(i)
            # Loop through tables in the section
            for j in range(section.Tables.Count):
                # Get a table
                table = section.Tables.get_Item(j)
                # Create a worksheet
                ws = wb.Worksheets.Add(f'Table_{i+1}_{j+1}')
                # Write the table to the worksheet
                for row in range(table.Rows.Count):
                    # Get a row
                    tableRow = table.Rows.get_Item(row)
                    # Loop through cells in the row
                    for cell in range(tableRow.Cells.Count):
                        # Get a cell
                        tableCell = tableRow.Cells.get_Item(cell)
                        # Get the text in the cell
                        cellText = ''
                        for paragraph in range(tableCell.Paragraphs.Count):
                            paragraph = tableCell.Paragraphs.get_Item(paragraph)
                            cellText = cellText + (paragraph.Text + ' ')
                        # Write the cell text to the worksheet
                        ws.SetCellValue(row + 1, cell + 1, cellText)

        # Save the workbook
        name = self.wordDoc.split("/")[-1]
        if self.saveFolder == None:
          wb.SaveToFile('/content/drive/MyDrive/CollectData/NER/excel/TestExamples/output/'+name+".xlsx", FileFormat.Version2016)
          nameFile = '/content/drive/MyDrive/CollectData/NER/excel/TestExamples/output/'+name+".xlsx"
        else:
          wb.SaveToFile(self.saveFolder+'/'+name+".xlsx", FileFormat.Version2016)
          nameFile = self.saveFolder+'/'+name + ".xlsx"
        doc.Close()
        wb.Dispose()
        return nameFile
      except: return "No table found on word doc"  
    else:
      return "No table found on word doc"     
  def getReference(self):
    pass
  def getSupMaterial(self):
    pass

import os
import requests
from spire.doc import Document
from spire.doc.common import *
from spire.xls import Workbook, FileFormat

class WordDocFast:
    _cache = {}  # Cache Document objects by file path/URL

    def __init__(self, wordDoc, saveFolder):
        self.wordDoc = wordDoc
        self.saveFolder = saveFolder or "."
        self.doc = self._load_document()

    def _load_document(self):
        # Use cache if available
        if self.wordDoc in WordDocFast._cache:
            return WordDocFast._cache[self.wordDoc]

        local_path = self.wordDoc
        if self.wordDoc.startswith("http"):
            name = os.path.basename(self.wordDoc)
            local_path = os.path.join(self.saveFolder, name)
            if not os.path.exists(local_path):
                r = requests.get(self.wordDoc, timeout=15)
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(r.content)

        doc = Document()
        doc.LoadFromFile(local_path)
        WordDocFast._cache[self.wordDoc] = doc
        return doc

    def extractText(self):
        """Extract full text (faster than page-by-page parsing)."""
        try:
          return self.doc.GetText()
        except:
          try:
            return self.extractTextBySections()
          except: 
            print("extract word doc text failed")
            return ''  
    def extractTextBySections(self):
        """Stream text section-by-section (can be faster for large docs)."""
        all_text = []
        for s in range(self.doc.Sections.Count):
            section = self.doc.Sections.get_Item(s)
            for p in range(section.Paragraphs.Count):
                text = section.Paragraphs.get_Item(p).Text.strip()
                if text:
                    all_text.append(text)
        return "\n".join(all_text)

    def extractTablesAsList(self):
        """Extract tables as list-of-lists (faster)."""
        tables = []
        for s in range(self.doc.Sections.Count):
            section = self.doc.Sections.get_Item(s)
            for t in range(section.Tables.Count):
                table = section.Tables.get_Item(t)
                table_data = []
                for r in range(table.Rows.Count):
                    row_data = []
                    for c in range(table.Rows.get_Item(r).Cells.Count):
                        cell = table.Rows.get_Item(r).Cells.get_Item(c)
                        cell_text = " ".join(
                            cell.Paragraphs.get_Item(p).Text.strip()
                            for p in range(cell.Paragraphs.Count)
                        ).strip()
                        row_data.append(cell_text)
                    table_data.append(row_data)
                tables.append(table_data)
        return tables

    def extractTablesAsExcel(self):
        """Export tables to Excel."""
        wb = Workbook()
        wb.Worksheets.Clear()
        for s in range(self.doc.Sections.Count):
            section = self.doc.Sections.get_Item(s)
            for t in range(section.Tables.Count):
                table = section.Tables.get_Item(t)
                ws = wb.Worksheets.Add(f"Table_{s+1}_{t+1}")
                for r in range(table.Rows.Count):
                    row = table.Rows.get_Item(r)
                    for c in range(row.Cells.Count):
                        cell = row.Cells.get_Item(c)
                        cell_text = " ".join(
                            cell.Paragraphs.get_Item(p).Text
                            for p in range(cell.Paragraphs.Count)
                        ).strip()
                        ws.SetCellValue(r + 1, c + 1, cell_text)
        name = os.path.basename(self.wordDoc) + ".xlsx"
        out_path = os.path.join(self.saveFolder, name)
        wb.SaveToFile(out_path, FileFormat.Version2016)
        wb.Dispose()
        return out_path    