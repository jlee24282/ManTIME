//package de.mpii.heideltime;

import com.google.gson.Gson;
import dataformat.Json;
import de.unihd.dbs.heideltime.standalone.DocumentType;
import de.unihd.dbs.heideltime.standalone.HeidelTimeStandalone;
import de.unihd.dbs.heideltime.standalone.OutputType;
import de.unihd.dbs.heideltime.standalone.POSTagger;
import de.unihd.dbs.heideltime.standalone.exceptions.DocumentCreationTimeMissingException;
import de.unihd.dbs.uima.annotator.heideltime.resources.Language;

import java.io.*;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class Nowigence {

    String dataFile = "";

    private List<String> getData(String inputFile) throws IOException {
        BufferedReader br = new BufferedReader(new FileReader(inputFile));
        String sCurrentLine;
        List<String> articles = new ArrayList<String>();

        //one line of json --> one article.
        while ((sCurrentLine = br.readLine()) != null) {
            articles.add(sCurrentLine);
        }
        return articles;
    }

    private void processData(List<String> articles) throws IOException, ParseException, DocumentCreationTimeMissingException {
        // some parameters
        OutputType outtype = OutputType.TIMEML;
        POSTagger postagger = POSTagger.TREETAGGER;
        // or: faster, but worse results; no TreeTagger required
        // POSTagger postagger = POSTagger.NO;
        String conffile = "conf/config.props";
        // initialize HeidelTime for English news
        HeidelTimeStandalone hsNews = new HeidelTimeStandalone(
                Language.ENGLISH,
                DocumentType.NEWS,
                outtype,
                conffile,
                postagger);
        int linenum = 0;
        for(String article: articles){

            Gson gson = new Gson();
            Json articleInfo = gson.fromJson(article, Json.class);

            // process English news (after handling DCT)
            String dctString = articleInfo.getEstimatedPublishedDate();
            String newsText = articleInfo.getContent();
            DateFormat df = new SimpleDateFormat("yyyy-MM-dd");
            Date dct = df.parse(dctString);
            String xmiNewsOutput = hsNews.process(newsText, dct);

            //write to output file
            String resultfName = dataFile.replace(".txt", "_"+linenum+".txt");linenum++;
            FileWriter fileWriter = new FileWriter("data/output_byline/output" + resultfName, true);
            System.err.println("NEWS*******" + xmiNewsOutput);
            System.out.println("------------------------------ test ends --------------------------------\n");
            fileWriter.write(xmiNewsOutput);
            fileWriter.close();


        }
    }

    private void nerProcess(String inputDir) throws DocumentCreationTimeMissingException, ParseException, IOException {

        //fielwriter for output
        FileWriter fileWriter = null;

        File directory = new File(inputDir);
        // get all the files from a directory
        File[] fList = directory.listFiles();
        List<String> listOfArticls = null;
        for (File file : fList) {
            //process each file one by one - > generate one resultfile for each input file.
            if (file.isFile() && !file.toString().contains(".DS_Store")) {
                this.dataFile = file.toString();
                dataFile = dataFile.replace("data/samples/", "");
                System.out.println(dataFile);
                //get data from txt file(json)
                listOfArticls = getData(file.toString());
                //process Data
                processData(listOfArticls);
            }
        }
    }

    public static void main(String[] args) throws DocumentCreationTimeMissingException, ParseException, IOException {
        final long startTime = System.currentTimeMillis();
        Nowigence ng = new Nowigence();
        //input directory
        String inputDir = "data/samples";
        ng.nerProcess(inputDir);
        final long endTime = System.currentTimeMillis();
        System.out.println("Total execution time: " + (endTime - startTime));
    }
}
