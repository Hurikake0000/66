from django import forms

class SearchForm(forms.Form):
    url = forms.URLField(label='URL', widget=forms.URLInput(attrs={'class': 'form-control'}))
    keyword = forms.CharField(label='Keyword', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
