//package de.mpii.heideltime;
import de.unihd.dbs.heideltime.standalone.DocumentType;
import de.unihd.dbs.heideltime.standalone.HeidelTimeStandalone;
import de.unihd.dbs.heideltime.standalone.OutputType;
import de.unihd.dbs.heideltime.standalone.POSTagger;
import de.unihd.dbs.heideltime.standalone.exceptions.DocumentCreationTimeMissingException;
import de.unihd.dbs.uima.annotator.heideltime.resources.Language;

import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class testHeideltime {
    public static void main(String[] args) throws
            DocumentCreationTimeMissingException, ParseException {
        // some parameters
        OutputType outtype = OutputType.XMI;
        POSTagger postagger = POSTagger.TREETAGGER;
        // or: faster, but worse results; no TreeTagger required
        // POSTagger postagger = POSTagger.NO;
        String conffile = "conf/config.props";
        // initialize HeidelTime for English news
        HeidelTimeStandalone hsNews = new HeidelTimeStandalone(Language.ENGLISH,
                DocumentType.NEWS, outtype, conffile, postagger);
        // initialize HeidelTime for English narrative
        HeidelTimeStandalone hsNarratives = new HeidelTimeStandalone(Language.ENGLISH,
                DocumentType.NARRATIVES, outtype, conffile, postagger);
        // process English narratives
        String narrativeText = "This is a text with a date in English: "
                + "January 24, 2009 and also two weeks later.";
        String xmiNarrativeOutput = hsNarratives.process(narrativeText);
        System.err.println("NARRATIVE*****" + xmiNarrativeOutput);
        // process English news (after handling DCT)
        String dctString = "2016-04-29";
        String newsText = "Today, I write a text with a date in English: "
                + "January 24, 2009 and also two weeks later. But what was two weeks ago?";
        DateFormat df = new SimpleDateFormat("yyyy-MM-dd");
        Date dct = df.parse(dctString);
        String xmiNewsOutput = hsNews.process(newsText, dct);
        System.err.println("NEWS*******" + xmiNewsOutput);
    }
}
