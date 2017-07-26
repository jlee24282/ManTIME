//package de.mpii.heideltime;

import de.unihd.dbs.heideltime.standalone.exceptions.DocumentCreationTimeMissingException;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.List;

public class ProcessOutput {

    String dataFile = "";
    public double totalTime = 0;
    public double totalEvent = 0;
    public double totalTtime = 0;
    public double totalTdate = 0;
    public double totalTSet = 0;
    public double totalTDur = 0;
    public double averageTime = 0;
    public double averageEvent = 0;
    public double averageTSet = 0;
    public double averageTDate = 0;
    public double averageTTime = 0;
    public double averageTDur = 0;
    public double absoluteCount = 0;

    public int docCount = 1;
    int error = 0;

    private List<String> getData(String inputFile) throws IOException {
        BufferedReader br = new BufferedReader(new FileReader(inputFile));
        String sCurrentLine;
        List<String> articles = new ArrayList<String>();

        while ((sCurrentLine = br.readLine()) != null) {
            articles.add(sCurrentLine);
        }
        return articles;
    }

    private void processData(List<String> results) throws IOException, ParseException, DocumentCreationTimeMissingException {
        int ocTimex3 = 0;
        int ocEvent = 0;
        int typeSet = 0;
        int typeDate = 0;
        int typeTime = 0;
        int typeDur = 0;

        for(String result: results){
            //find the Timex3 calculate
            ocTimex3 = result.split("heideltime:Timex3").length - 1;
            ocEvent = result.split("EVENT").length-1;
            typeSet = result.split("SET").length-1;
            typeDate = result.split("DATE").length-1;
            typeTime = result.split("TIME").length-1;
            typeDur = result.split("DUR").length-1;
            //calculate average
            absoluteCount += ocTimex3;
            totalTime += ocTimex3;
            averageTime = totalTime/docCount;
            totalEvent += ocEvent;
            averageEvent = totalEvent/docCount;
            totalTSet += typeSet;
            averageTSet = totalTSet/docCount;
            totalTdate += typeDate;
            averageTDate = totalTdate/docCount;
            totalTtime += typeTime;
            averageTTime = totalTtime/docCount;
            totalTDur += typeDur;
            averageTDur = totalTDur/docCount;
            docCount++;

            if (ocTimex3 == 0){
                error++;
            }

            //print result for everything.
//            System.out.println(docCount + " ocTime: " + ocTimex3);
//            System.out.println(docCount + " ocEvent: " + ocEvent);
//            System.out.println(docCount + " typeDate: " + typeDate);
//            System.out.println(docCount + " typeSet: " + typeSet);
//            System.out.println(docCount + " totalTDur: " + totalTDur);
//            System.out.println(docCount + " totalTSet: " + totalTSet);
//            System.out.println(docCount + " totalTdate: " + totalTdate/docCount);
//            System.out.println(docCount + " Average Timex3: " + averageTime);
//            System.out.println(docCount + " Average Event: " + averageEvent);
//            System.out.println(docCount + " Average Set: " + averageTSet);
//            System.out.println(docCount + " Average Date: " + averageTDate);
//            System.out.println(docCount + " Average Type: " + averageTTime);
//            System.out.println(docCount + " Average Dur: " + averageTDur);
            System.out.println(docCount + " Absolute Count: " + absoluteCount);
            System.out.println(docCount + " Absolute Count SET: " + totalTSet);
            System.out.println(docCount + " Absolute Count DUR: " + totalTDur);
            System.out.println(docCount + " Absolute Count TIME: " + totalTime);
            System.out.println(docCount + " Absolute Count DATE: " + totalTdate);
            System.out.println(docCount + " Doc Count: " + docCount);


            System.out.println("------------------------------ test ends --------------------------------\n");
        }
        System.out.println(error);
    }

    int word_count(String text,String key){
        int count=0;
        while(text.contains(key)){
            count++;
            text=text.substring(text.indexOf(key)+key.length());
        }
        return count;
    }

    private void nerProcess(String inputDir) throws DocumentCreationTimeMissingException, ParseException, IOException {
        //fielwriter for output

        File directory = new File(inputDir);
        // get all the files from a directory
        File[] fList = directory.listFiles();
        List<String> listOfArticls = null;
        for (File file : fList) {
            System.out.println(file.toString());
            //process each file one by one - > generate one resultfile for each input file.
            if (file.isFile() && file.toString().contains(".txt")) {
                this.dataFile = file.toString();
                dataFile = dataFile.replace(inputDir, "");
                System.out.println(dataFile);
                //get data from txt file(json)
                listOfArticls = getData(file.toString());
                //process Data
                processData(listOfArticls);
            }
        }
    }

    public static void main(String[] args) throws DocumentCreationTimeMissingException, ParseException, IOException {
        System.out.printf("tes");
        ProcessOutput test = new ProcessOutput();
        //input directory
        String inputDir = "data/output_byline";
        test.nerProcess(inputDir);
    }
}
