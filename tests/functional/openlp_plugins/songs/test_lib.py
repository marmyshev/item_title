"""
This module contains tests for the lib submodule of the Songs plugin.
"""

from unittest import TestCase

from mock import patch, MagicMock

from openlp.plugins.songs.lib import VerseType, clean_string, clean_title
from openlp.plugins.songs.lib.songcompare import songs_probably_equal, _remove_typos, _op_length


class TestLib(TestCase):
    """
    Test the functions in the :mod:`lib` module.
    """
    def setUp(self):
        """
        Mock up two songs and provide a set of lyrics for the songs_probably_equal tests.
        """
        self.full_lyrics ='''amazing grace how sweet the sound that saved a wretch like me i once was lost but now am
            found was blind but now i see  twas grace that taught my heart to fear and grace my fears relieved how
            precious did that grace appear the hour i first believed  through many dangers toils and snares i have already
            come tis grace that brought me safe thus far and grace will lead me home'''
        self.short_lyrics ='''twas grace that taught my heart to fear and grace my fears relieved how precious did that
            grace appear the hour i first believed'''
        self.error_lyrics ='''amazing how sweet the trumpet that saved a wrench like me i once was losst but now am
            found waf blind but now i see  it was grace that taught my heart to fear and grace my fears relieved how
            precious did that grace appppppppear the hour i first believedxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx snares i have
            already come to this grace that brought me safe so far and grace will lead me home'''
        self.different_lyrics='''on a hill far away stood an old rugged cross the emblem of suffering and shame and i love
            that old cross where the dearest and best for a world of lost sinners was slain  so ill cherish the old rugged
            cross till my trophies at last i lay down i will cling to the old rugged cross and exchange it some day for a
            crown'''
        self.song1 = MagicMock()
        self.song2 = MagicMock()

    def clean_string_test(self):
        """
        Test the clean_string() function
        """
        # GIVEN: A "dirty" string
        dirty_string = 'Ain\'t gonna   find\t you there.'

        # WHEN: We run the string through the function
        result = clean_string(dirty_string)

        # THEN: The string should be cleaned up and lower-cased
        self.assertEqual(result, 'aint gonna find you there ', 'The string should be cleaned up properly')

    def clean_title_test(self):
        """
        Test the clean_title() function
        """
        # GIVEN: A "dirty" string
        dirty_string = 'This\u0000 is a\u0014 dirty \u007Fstring\u009F'

        # WHEN: We run the string through the function
        result = clean_title(dirty_string)

        # THEN: The string should be cleaned up
        self.assertEqual(result, 'This is a dirty string', 'The title should be cleaned up properly: "%s"' % result)

    def songs_probably_equal_same_song_test(self):
        """
        Test the songs_probably_equal function with twice the same song.
        """
        # GIVEN: Two equal songs.
        self.song1.search_lyrics = self.full_lyrics
        self.song2.search_lyrics = self.full_lyrics
        
        # WHEN: We compare those songs for equality.
        result = songs_probably_equal(self.song1, self.song2)
        
        # THEN: The result should be True.
        assert result == True, 'The result should be True'

    def songs_probably_equal_short_song_test(self):
        """
        Test the songs_probably_equal function with a song and a shorter version of the same song.
        """
        # GIVEN: A song and a short version of the same song.
        self.song1.search_lyrics = self.full_lyrics
        self.song2.search_lyrics = self.short_lyrics
        
        # WHEN: We compare those songs for equality.
        result = songs_probably_equal(self.song1, self.song2)
        
        # THEN: The result should be True.
        assert result == True, 'The result should be True'

    def songs_probably_equal_error_song_test(self):
        """
        Test the songs_probably_equal function with a song and a  very erroneous version of the same song.
        """
        # GIVEN: A song and the same song with lots of errors.
        self.song1.search_lyrics = self.full_lyrics
        self.song2.search_lyrics = self.error_lyrics
        
        # WHEN: We compare those songs for equality.
        result = songs_probably_equal(self.song1, self.song2)
        
        # THEN: The result should be True.
        assert result == True, 'The result should be True'

    def songs_probably_equal_different_song_test(self):
        """
        Test the songs_probably_equal function with two different songs.
        """
        # GIVEN: Two different songs.
        self.song1.search_lyrics = self.full_lyrics
        self.song2.search_lyrics = self.different_lyrics
        
        # WHEN: We compare those songs for equality.
        result = songs_probably_equal(self.song1, self.song2)
        
        # THEN: The result should be False.
        assert result == False, 'The result should be False'

    def remove_typos_beginning_test(self):
        """
        Test the _remove_typos function with a typo at the beginning.
        """
        # GIVEN: A diffset with a difference at the beginning.
        diff = [('replace', 0, 2, 0, 1), ('equal', 2, 11, 1, 10)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(diff)

        # THEN: There should be no typos at the beginning anymore.
        assert len(result) == 1, 'The result should contain only one element.'
        assert result[0][0] == 'equal', 'The result should contain an equal element.'

    def remove_typos_beginning_negated_test(self):
        """
        Test the _remove_typos function with a large difference at the beginning.
        """
        # GIVEN: A diffset with a large difference at the beginning.
        diff = [('replace', 0, 20, 0, 1), ('equal', 20, 29, 1, 10)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(list(diff))

        # THEN: There diff should not have changed.
        assert result == diff

    def remove_typos_end_test(self):
        """
        Test the _remove_typos function with a typo at the end.
        """
        # GIVEN: A diffset with a difference at the end.
        diff = [('equal', 0, 10, 0, 10), ('replace', 10, 12, 10, 11)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(diff)

        # THEN: There should be no typos at the end anymore.
        assert len(result) == 1, 'The result should contain only one element.'
        assert result[0][0] == 'equal', 'The result should contain an equal element.'

    def remove_typos_end_negated_test(self):
        """
        Test the _remove_typos function with a large difference at the end.
        """
        # GIVEN: A diffset with a large difference at the end.
        diff = [('equal', 0, 10, 0, 10), ('replace', 10, 20, 10, 1)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(list(diff))

        # THEN: There diff should not have changed.
        assert result == diff

    def remove_typos_middle_test(self):
        """
        Test the _remove_typos function with a typo in the middle.
        """
        # GIVEN: A diffset with a difference in the middle.
        diff = [('equal', 0, 10, 0, 10), ('replace', 10, 12, 10, 11), ('equal', 12, 22, 11, 21)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(diff)

        # THEN: There should be no typos in the middle anymore. The remaining equals should have been merged.
        assert len(result) is 1, 'The result should contain only one element.'
        assert result[0][0] == 'equal', 'The result should contain an equal element.'
        assert result[0][1] == 0, 'The start indices should be kept.'
        assert result[0][2] == 22, 'The stop indices should be kept.'
        assert result[0][3] == 0, 'The start indices should be kept.'
        assert result[0][4] == 21, 'The stop indices should be kept.'

    def remove_typos_beginning_negated_test(self):
        """
        Test the _remove_typos function with a large difference in the middle.
        """
        # GIVEN: A diffset with a large difference in the middle.
        diff = [('equal', 0, 10, 0, 10), ('replace', 10, 20, 10, 11), ('equal', 20, 30, 11, 21)]

        # WHEN: We remove the typos in there.
        result = _remove_typos(list(diff))

        # THEN: There diff should not have changed.
        assert result == diff

    def op_length_test(self):
        """
        Test the _op_length function.
        """
        # GIVEN: A diff entry.
        diff_entry = ('replace', 0, 2, 4, 14)

        # WHEN: We calculate the length of that diff.
        result = _op_length(diff_entry)

        # THEN: The maximum length should be returned.
        assert result == 10, 'The length should be 10.'


class TestVerseType(TestCase):
    """
    This is a test case to test various methods in the VerseType enumeration class.
    """

    def translated_tag_test(self):
        """
        Test that the translated_tag() method returns the correct tags
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_tag() method with a "verse"
            result = VerseType.translated_tag('v')

            # THEN: The result should be "V"
            self.assertEqual(result, 'V', 'The result should be "V"')

            # WHEN: We run the translated_tag() method with a "chorus"
            result = VerseType.translated_tag('c')

            # THEN: The result should be "C"
            self.assertEqual(result, 'C', 'The result should be "C"')

    def translated_invalid_tag_test(self):
        """
        Test that the translated_tag() method returns the default tag when passed an invalid tag
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_tag() method with an invalid verse type
            result = VerseType.translated_tag('z')

            # THEN: The result should be "O"
            self.assertEqual(result, 'O', 'The result should be "O", but was "%s"' % result)

    def translated_invalid_tag_with_specified_default_test(self):
        """
        Test that the translated_tag() method returns the specified default tag when passed an invalid tag
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_tag() method with an invalid verse type and specify a default
            result = VerseType.translated_tag('q', VerseType.Bridge)

            # THEN: The result should be "B"
            self.assertEqual(result, 'B', 'The result should be "B", but was "%s"' % result)

    def translated_invalid_tag_with_invalid_default_test(self):
        """
        Test that the translated_tag() method returns a sane default tag when passed an invalid default
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_tag() method with an invalid verse type and an invalid default
            result = VerseType.translated_tag('q', 29)

            # THEN: The result should be "O"
            self.assertEqual(result, 'O', 'The result should be "O", but was "%s"' % result)

    def translated_name_test(self):
        """
        Test that the translated_name() method returns the correct name
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_name() method with a "verse"
            result = VerseType.translated_name('v')

            # THEN: The result should be "Verse"
            self.assertEqual(result, 'Verse', 'The result should be "Verse"')

            # WHEN: We run the translated_name() method with a "chorus"
            result = VerseType.translated_name('c')

            # THEN: The result should be "Chorus"
            self.assertEqual(result, 'Chorus', 'The result should be "Chorus"')

    def translated_invalid_name_test(self):
        """
        Test that the translated_name() method returns the default name when passed an invalid tag
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_name() method with an invalid verse type
            result = VerseType.translated_name('z')

            # THEN: The result should be "Other"
            self.assertEqual(result, 'Other', 'The result should be "Other", but was "%s"' % result)

    def translated_invalid_name_with_specified_default_test(self):
        """
        Test that the translated_name() method returns the specified default name when passed an invalid tag
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_name() method with an invalid verse type and specify a default
            result = VerseType.translated_name('q', VerseType.Bridge)

            # THEN: The result should be "Bridge"
            self.assertEqual(result, 'Bridge', 'The result should be "Bridge", but was "%s"' % result)

    def translated_invalid_name_with_invalid_default_test(self):
        """
        Test that the translated_name() method returns the specified default tag when passed an invalid tag
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the translated_name() method with an invalid verse type and specify an invalid default
            result = VerseType.translated_name('q', 29)

            # THEN: The result should be "Other"
            self.assertEqual(result, 'Other', 'The result should be "Other", but was "%s"' % result)

    def from_tag_test(self):
        """
        Test that the from_tag() method returns the correct VerseType.
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the from_tag() method with a valid verse type, we get the name back
            result = VerseType.from_tag('v')

            # THEN: The result should be VerseType.Verse
            self.assertEqual(result, VerseType.Verse, 'The result should be VerseType.Verse, but was "%s"' % result)

    def from_tag_with_invalid_tag_test(self):
        """
        Test that the from_tag() method returns the default VerseType when it is passed an invalid tag.
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the from_tag() method with a valid verse type, we get the name back
            result = VerseType.from_tag('w')

            # THEN: The result should be VerseType.Other
            self.assertEqual(result, VerseType.Other, 'The result should be VerseType.Other, but was "%s"' % result)

    def from_tag_with_specified_default_test(self):
        """
        Test that the from_tag() method returns the specified default when passed an invalid tag.
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the from_tag() method with an invalid verse type, we get the specified default back
            result = VerseType.from_tag('x', VerseType.Chorus)

            # THEN: The result should be VerseType.Chorus
            self.assertEqual(result, VerseType.Chorus, 'The result should be VerseType.Chorus, but was "%s"' % result)

    def from_tag_with_invalid_default_test(self):
        """
        Test that the from_tag() method returns a sane default when passed an invalid tag and an invalid default.
        """
        # GIVEN: A mocked out translate() function that just returns what it was given
        with patch('openlp.plugins.songs.lib.translate') as mocked_translate:
            mocked_translate.side_effect = lambda x, y: y

            # WHEN: We run the from_tag() method with an invalid verse type, we get the specified default back
            result = VerseType.from_tag('m', 29)

            # THEN: The result should be VerseType.Other
            self.assertEqual(result, VerseType.Other, 'The result should be VerseType.Other, but was "%s"' % result)
